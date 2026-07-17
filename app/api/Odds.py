import pandas as pd
import difflib

from app.api.ModelPredictor import ModelPredictor


class Odds:

    __odds_dataset: pd.DataFrame
    __match_dataset: pd.DataFrame
    __merged_dataset: pd.DataFrame

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

        # Risoluzione dei nomi delle squadre
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

        # Affiancamento dei due dataset
        self.__merged_dataset = pd.merge(
            left=self.__match_dataset,
            right=self.__odds_dataset,
            left_on=['Match_Date_Temp', 'HomeTeam', 'AwayTeam'],
            right_on=['Odds_Date_Temp', 'homeTeam_Norm', 'awayTeam_Norm'],
            how='inner' 
        )

        # Pulizia delle colonne temporanee create per il merge
        col_rimuovere_match = ['Match_Date_Temp']
        col_rimuovere_odds = ['Odds_Date_Temp', 'homeTeam_Norm', 'awayTeam_Norm']
        
        # Le puliamo sia dai dataset originali che dal dataset finale
        self.__match_dataset.drop(columns=col_rimuovere_match, inplace=True, errors='ignore')
        self.__odds_dataset.drop(columns=col_rimuovere_odds, inplace=True, errors='ignore')
        self.__merged_dataset.drop(columns=col_rimuovere_match + col_rimuovere_odds, inplace=True, errors='ignore')

    def __init__(
            self,
            odds_dataframe_path: str,
            match_dataframe_path: str
    ) -> None:

        # Importazione e rimozione delle rows vuote 
        self.__odds_dataset = pd.read_csv(odds_dataframe_path)
        self.__match_dataset = pd.read_csv(match_dataframe_path)
        self.__odds_dataset = self.__odds_dataset.dropna()

        # Merge dei due dataset
        self.__merge_dataset()
        print(self.__merged_dataset.head(10))

    

    def backtest(self, season: int) -> list[float]:
        """
        Metodo che permette di fare un 'backtest' del modello selezionato...
        """
        import numpy as np

        # Ottengo le row della stagione inserita
        selected_df = self.__merged_dataset[self.__merged_dataset["Season_x"] == f"{season}-{season+1}"]
        
        n_matches = len(selected_df)
        if n_matches == 0:
            return [0.0, 0.0, 0.0, 0.0]

        # 1. RISOLUZIONE BUG MATEMATICO: 
        # Il costo iniziale non è fisso a -3800, ma dipende dalle partite REALI giocate nel dataframe.
        costo_totale_scommesse = -10.0 * n_matches
        earns = [costo_totale_scommesse] * 4

        # Inizializzazione modelli (Consiglio: spostali in __init__ per non ricaricarli dal disco ogni volta!)
        models = [
            ModelPredictor("app/static/models/linear_model.joblib"),
            ModelPredictor("app/static/models/random_forest_model.joblib"),
            ModelPredictor("app/static/models/random_xgboost_model.joblib"),
        ]
        
        # 2. OTTIMIZZAZIONE PRESTAZIONI: Vettorializzazione delle features
        # Prepariamo le matrici di input (tutte le righe in un solo colpo)
        X1 = np.column_stack((
            selected_df["Home_WinStreak"] - selected_df["Away_WinStreak"],
            selected_df["GoalOnShotRatioHome"] - selected_df["GoalOnShotRatioAway"],
            selected_df["HomeElo"] - selected_df["AwayElo"],
            selected_df["HomeAdvantage"],
            selected_df["Z_Home_Goals_Season"] - selected_df["Z_Away_Goals_Season"],
            np.abs(selected_df["Home_Current_Points"] - selected_df["Away_Current_Points"])
        ))

        X2 = np.column_stack((
            selected_df["HomeValue"] - selected_df["AwayValue"],
            selected_df["Z_Home_Wins_Season"] - selected_df["Z_Away_Wins_Season"],
            np.abs(selected_df["HomeValue"] - selected_df["AwayValue"]),
            selected_df["HomeAdvantage"]
        ))

        X3 = np.column_stack((
            selected_df["HomeValue"] - selected_df["AwayValue"],
            selected_df["Z_Home_Wins_Season"] - selected_df["Z_Away_Wins_Season"],
            np.abs(selected_df["HomeValue"] - selected_df["AwayValue"])
        ))

        # Eseguiamo le previsioni in batch (una passata singola, velocissimo)
        m1_prev_batch = models[0].predict(X1)
        m2_prev_batch = models[1].predict(X2)
        m3_prev_batch = models[2].predict(X3)

        # Previsioni Baseline (Random) vettorializzate
        baseline_preds = np.random.randint(0, 3, size=n_matches)

        # 3. LOGICA DI SCELTA VETTORIALIZZATA (Sostituisce il tuo if/else con np.where)
        # np.where(condizione, valore_se_vero, valore_se_falso)
        res_1 = np.where(m1_prev_batch[:, 1] > 0.27, 1, np.argmax(m1_prev_batch, axis=1))
        res_2 = np.where(m2_prev_batch[:, 1] > 0.29, 1, np.argmax(m2_prev_batch, axis=1))
        res_3 = np.where(m3_prev_batch[:, 1] > 0.29, 1, np.argmax(m3_prev_batch, axis=1))

        # 4. CALCOLO DEI GUADAGNI OTTIMIZZATO
        mapping_risultati = np.array(['H', 'D', 'A'])
        risultati_reali = selected_df['FTR'].values
        
        # Estraiamo le quote come un'unica matrice (N_partite, 3_esiti)
        quote_matrice = np.column_stack((
            selected_df['H'].astype(float).values, 
            selected_df['D'].astype(float).values, 
            selected_df['A'].astype(float).values
        ))

        def calcola_vincita_modello(previsioni_indici):
            # Convertiamo gli indici (0,1,2) in stringhe ('H', 'D', 'A')
            previsioni_str = mapping_risultati[previsioni_indici]
            
            # Maschera booleana: in quali partite abbiamo indovinato?
            vittorie = (previsioni_str == risultati_reali)
            
            # Peschiamo le quote esatte giocate per ogni partita 
            # np.arange(n_matches) seleziona la riga, previsioni_indici seleziona la colonna corretta (H=0, D=1, A=2)
            quote_giocate = quote_matrice[np.arange(n_matches), previsioni_indici]
            
            # Moltiplichiamo le quote delle SOLI partite vinte per 10€ e le sommiamo
            return np.sum(10.0 * quote_giocate[vittorie])

        # Aggiorniamo i guadagni finali
        earns[0] += calcola_vincita_modello(baseline_preds)
        earns[1] += calcola_vincita_modello(res_1)
        earns[2] += calcola_vincita_modello(res_2)
        earns[3] += calcola_vincita_modello(res_3)

        return earns

        
