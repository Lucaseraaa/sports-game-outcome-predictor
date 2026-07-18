import os
import difflib
import pandas as pd
import numpy as np
from app.constants import LINEAR_TRESHOLD, XGBOOST_TRESHOLD, FOREST_TRESHOLD
from app.api.ModelPredictor import ModelPredictor

class Odds:
    __odds_dataset: pd.DataFrame
    __match_dataset: pd.DataFrame
    __merged_dataset: pd.DataFrame

    def __init__(self, odds_dataframe_path: str, match_dataframe_path: str) -> None:
        self.__odds_dataset = pd.read_csv(odds_dataframe_path)
        self.__match_dataset = pd.read_csv(match_dataframe_path)
        self.__odds_dataset = self.__odds_dataset.dropna()
        self.__merge_dataset()

    def __merge_dataset(self) -> None:

        # Normalizzazione delle date
        self.__match_dataset['Match_Date_Temp'] = pd.to_datetime(
            self.__match_dataset['Date'], 
            errors='coerce' 
        ).dt.date

        self.__odds_dataset['Odds_Date_Temp'] = pd.to_datetime(
            self.__odds_dataset['matchDate'], 
            format="%d-%m-%y %H:%M", 
            errors='coerce' 
        ).dt.date

        self.__match_dataset = self.__match_dataset.dropna(subset=['Match_Date_Temp'])
        self.__odds_dataset = self.__odds_dataset.dropna(subset=['Odds_Date_Temp'])
        
        match_teams = pd.concat([self.__match_dataset['HomeTeam'], self.__match_dataset['AwayTeam']]).unique()
        odds_teams = pd.concat([self.__odds_dataset['homeTeam'], self.__odds_dataset['awayTeam']]).unique()

        team_mapping = {}
        for team in odds_teams:
            matches = difflib.get_close_matches(team, match_teams, n=1, cutoff=0.5)
            team_mapping[team] = matches[0] if matches else team

        self.__odds_dataset['homeTeam_Norm'] = self.__odds_dataset['homeTeam'].map(team_mapping)
        self.__odds_dataset['awayTeam_Norm'] = self.__odds_dataset['awayTeam'].map(team_mapping)

        self.__merged_dataset = pd.merge(
            left=self.__match_dataset,
            right=self.__odds_dataset,
            left_on=['Match_Date_Temp', 'HomeTeam', 'AwayTeam'],
            right_on=['Odds_Date_Temp', 'homeTeam_Norm', 'awayTeam_Norm'],
            how='inner' 
        )

        col_rimuovere_match = ['Match_Date_Temp']
        col_rimuovere_odds = ['Odds_Date_Temp', 'homeTeam_Norm', 'awayTeam_Norm']
        
        self.__match_dataset.drop(columns=col_rimuovere_match, inplace=True, errors='ignore')
        self.__odds_dataset.drop(columns=col_rimuovere_odds, inplace=True, errors='ignore')
        self.__merged_dataset.drop(columns=col_rimuovere_match + col_rimuovere_odds, inplace=True, errors='ignore')

    def backtest(self, season_str: str, budget_iniziale: float, puntata_fissa: float) -> dict:

        # Identifica la colonna corretta della stagione per evitare KeyError
        colonna_stagione = "Season_x" if "Season_x" in self.__merged_dataset.columns else "Season"
        
        selected_df = self.__merged_dataset[self.__merged_dataset[colonna_stagione] == season_str]
        
        n_matches = len(selected_df)
        if n_matches == 0:
            return {
                "totale": 0, "storico_rf": [],
                "flow_rf": [budget_iniziale], "flow_logistic": [budget_iniziale], "flow_xgb": [budget_iniziale]
            }

        models = [
            ModelPredictor("app/static/models/linear_model.joblib"),
            ModelPredictor("app/static/models/random_forest_model.joblib"),
            ModelPredictor("app/static/models/random_xgboost_model.joblib"),
        ]
        
        
        
        X1 = pd.DataFrame({
            "WinStreak": selected_df["Home_WinStreak"] - selected_df["Away_WinStreak"],
            "GoalOnShotRatio": selected_df["GoalOnShotRatioHome"] - selected_df["GoalOnShotRatioAway"],
            "Elo": selected_df["HomeElo"] - selected_df["AwayElo"],
            "HomeAdvantage": selected_df["HomeAdvantage"],
            "Z_Goals_Season": selected_df["Z_Home_Goals_Season"] - selected_df["Z_Away_Goals_Season"],
            "Abs_Points_Difference": np.abs(selected_df["Home_Current_Points"] - selected_df["Away_Current_Points"])
        })

        X2 = pd.DataFrame({
            "Value": selected_df["HomeValue"] - selected_df["AwayValue"],
            "Z_Wins_Season": selected_df["Z_Home_Wins_Season"] - selected_df["Z_Away_Wins_Season"],
            "Abs_Value_Difference": np.abs(selected_df["HomeValue"] - selected_df["AwayValue"]),
            "HomeAdvantage": selected_df["HomeAdvantage"]
        })

        X3 = pd.DataFrame({
            "Value": selected_df["HomeValue"] - selected_df["AwayValue"],
            "Z_Wins_Season": selected_df["Z_Home_Wins_Season"] - selected_df["Z_Away_Wins_Season"],
            "Abs_Value_Difference": np.abs(selected_df["HomeValue"] - selected_df["AwayValue"])
        })

        # Inferenza
        m1_prev = models[0].predict(X1)
        m2_prev = models[1].predict(X2)
        m3_prev = models[2].predict(X3)

        # Scelta del segno con correzione degli argmax associati a ciascun modello
        res_1 = np.where(m1_prev[:, 1] > LINEAR_TRESHOLD, 1, np.argmax(m1_prev, axis=1))
        res_2 = np.where(m2_prev[:, 1] > FOREST_TRESHOLD, 1, np.argmax(m2_prev, axis=1))
        res_3 = np.where(m3_prev[:, 1] > XGBOOST_TRESHOLD, 1, np.argmax(m3_prev, axis=1))

        mapping_risultati = np.array(['1', 'X', '2'])
        ftr_mapping = {'H': '1', 'D': 'X', 'A': '2'}
        risultati_reali = selected_df['FTR'].map(ftr_mapping).values
        
        quote_matrice = np.column_stack((
            selected_df['H'].astype(float).values, 
            selected_df['D'].astype(float).values, 
            selected_df['A'].astype(float).values
        ))

        pred_linear_arr = mapping_risultati[res_1]
        pred_forest_arr = mapping_risultati[res_2]
        pred_xgb_arr = mapping_risultati[res_3]

        flow_rf = [budget_iniziale]
        flow_logistic = [budget_iniziale]
        flow_xgb = [budget_iniziale]
        storico_rf_dettagliato = []

        teams_home = selected_df['HomeTeam'].values
        teams_away = selected_df['AwayTeam'].values

        for i in range(n_matches):
            real_sign = risultati_reali[i]
            
            # Random Forest
            pred_rf = pred_forest_arr[i]
            quota_rf = quote_matrice[i, res_2[i]]
            esito_rf = "Vinta" if pred_rf == real_sign else "Persa"
            guadagno_rf = (puntata_fissa * quota_rf) - puntata_fissa if esito_rf == "Vinta" else -puntata_fissa
            flow_rf.append(flow_rf[-1] + guadagno_rf)

            storico_rf_dettagliato.append({
                "match": f"{teams_home[i]} - {teams_away[i]}",
                "prediction": pred_rf,
                "quota": round(quota_rf, 2),
                "esito": esito_rf,
                "guadagno": round(guadagno_rf, 2),
                "bilancio_flow": round(flow_rf[-1], 2)
            })

            # Regressione Logistica
            pred_log = pred_linear_arr[i]
            quota_log = quote_matrice[i, res_1[i]]
            guadagno_log = (puntata_fissa * quota_log) - puntata_fissa if pred_log == real_sign else -puntata_fissa
            flow_logistic.append(flow_logistic[-1] + guadagno_log)

            # XGBoost
            pred_xgb = pred_xgb_arr[i]
            quota_xgb = quote_matrice[i, res_3[i]]
            guadagno_xgb = (puntata_fissa * quota_xgb) - puntata_fissa if pred_xgb == real_sign else -puntata_fissa
            flow_xgb.append(flow_xgb[-1] + guadagno_xgb)

        return {
            "totale": n_matches,
            "storico_rf": storico_rf_dettagliato,
            "flow_rf": flow_rf,
            "flow_logistic": flow_logistic,
            "flow_xgb": flow_xgb
        }