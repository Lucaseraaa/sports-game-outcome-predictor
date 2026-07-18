from datetime import datetime, timedelta
import time
from flask.views import MethodView
from flask import render_template, request
import numpy as np
import pandas as pd
from app.api.SoccerDataApi import SoccerDataApi
from app.api.ModelPredictor import ModelPredictor  
from app.api.MatchesDatasetEditor import MatchesDatasetEditor  
from app.models.Statistics import Statistics
from app.models.Team import Team

class HomeView(MethodView):
    __dataset_editor: MatchesDatasetEditor
    __predictor: ModelPredictor

    def __init__(self):
        super().__init__()
        
        # Caricamento del modello Random Forest
        try:
            self.__predictor = ModelPredictor("app/static/models/random_forest_model.joblib")
        except Exception as e:
            print(f"Errore nel caricamento del modello Random Forest: {e}")
            self.__predictor = None
        # Caricamento del Dataset Editor
        try:
            self.__dataset_editor = MatchesDatasetEditor("app/static/result.csv")
        except Exception as e:
            print(f"Errore nel caricamento del MatchesDatasetEditor: {e}")
            self.__dataset_editor = None

    def _calcola_segno_e_probabilita(self, probabilities) -> tuple:
        """
        Prende l'output di predict_proba e restituisce le percentuali e il segno predetto
        basandosi sulle tue specifiche regole di business.
        """
        probs = probabilities[0]
        
        p1 = int(round(probs[0] * 100))
        px = int(round(probs[1] * 100))
        p2 = int(round(probs[2] * 100))
        
        # Correzione arrotondamento 
        differenza = 100 - (p1 + px + p2)
        p1 += differenza 
        # Se la probabilità del pareggio (px) è >= 29%, predice "X"
        if px >= 29:
            prediction = "X"
        else:
            # Altrimenti predice il massimo tra 1 e 2
            if p1 >= p2:
                prediction = "1"
            else:
                prediction = "2"
                
        return prediction, p1, px, p2

    def __extract_match_features(self, home_team: str, away_team: str, match_day: str, day: int, api_client: SoccerDataApi):
        """
        Metodo utilizzato per poplare ed estrarre i dati dal dataframe.
        Logica migliorata:
        - Se non esiste: aggiungi con valori default (Value=0)
        - Se esiste ma valori mancanti (soprattutto risultati o Values): aggiorna tramite API
        """
        match_date = datetime.strptime(match_day, "%Y-%m-%d")
        today = datetime.now().date()
        match_date_only = match_date.date()

        # Verifica esistenza
        if not self.__dataset_editor.is_in_dataset(match_day, home_team, away_team):
            # Aggiungi record base con Value=0
            self.__dataset_editor.add_match_in_dataset(day, home_team, away_team, match_day)
            print(f"Record aggiunto per {home_team} vs {away_team} con Values=0")

        # Estrai record corrente
        record = self.__dataset_editor.extract_from_dataset(match_day, home_team, away_team)
        
        needs_update = False
        update_values = False
        update_results = False

        # Controlla se servono aggiornamenti
        if record is not None:
            # Controlli per Values (aggiorna solo vicino alla data della partita)
            if (record.get("HomeValue", 0) == 0 or record.get("AwayValue", 0) == 0) and \
               abs((match_date_only - today).days) <= 1:  # Giorno stesso o giorno prima
                update_values = True
                needs_update = True
            
            # Controlli per risultati finali (se partita passata)
            if match_date_only < today and (pd.isna(record.get("FTHG")) or pd.isna(record.get("FTAG")) or record.get("FTR") in [None, '', ' ']):
                update_results = True
                needs_update = True

        if needs_update:
            # Cerca match_id tramite API (necessario per get_match_detail e get_match_teams_value)
            match_id = self.__find_match_id(api_client, home_team, away_team, match_day)
            if match_id:
                if update_values:
                    try:
                        player_stats = api_client.get_match_teams_value(match_id)
                        self.__dataset_editor.update_match_values(
                            match_day, home_team, away_team,
                            player_stats.homePlayersValue,
                            player_stats.awayPlayersValue
                        )
                        print(f"Values aggiornati per {home_team} vs {away_team}")
                    except Exception as e:
                        print(f"Errore update Values: {e}")

                if update_results:
                    try:
                        stats = api_client.get_match_detail(match_id)
                        self.__dataset_editor.update_match_results(
                            match_day, home_team, away_team,
                            stats.homeGoal, stats.awayGoal, stats.fullTimeResult
                        )
                        print(f"Risultati aggiornati per {home_team} vs {away_team}")
                    except Exception as e:
                        print(f"Errore update risultati: {e}")

        # Ritorna record aggiornato
        return self.__dataset_editor.extract_from_dataset(match_day, home_team, away_team)

    def __find_match_id(self, api_client: SoccerDataApi, home_team: str, away_team: str, match_date: str) -> int | None:
        """Helper per trovare l'ID di un match tramite API (da implementare in SoccerDataApi se non esiste)"""
        try:
            # Per semplicità, chiama get_matches e cerca per data/squadre
            season = int(match_date[:4])
            day = 1  # Placeholder - ottimizza se possibile
            matches = api_client.get_matches(season=season, day=day)
            if matches and hasattr(matches, 'data'):
                for m in matches.data:
                    if (m.homeTeam.name == home_team or m.awayTeam.name == away_team) and \
                       m.date.startswith(match_date):
                        return getattr(m, 'id', None)
            return None
        except Exception as e:
            print(f"Errore ricerca match_id: {e}")
            return None

    

    def get(self):
        from datetime import datetime
    
        stagione_stringa = request.args.get('anno', '2026-2027')
        giornata_stringa = request.args.get('giornata', '1')
        
        season_int = int(stagione_stringa.split('-')[0])
        requested_day = int(giornata_stringa)
        
        api_client = SoccerDataApi()
        
        day_int = requested_day
        
        # Ricerco le partite della giornata dal dataset 
        matches = self.__dataset_editor.get_all_match_of_day(stagione_stringa, day_int)

        if len(matches) != 10:
            
            try:

                # Chiamata API per i match
                matches_pydantic = api_client.get_matches(season=season_int, day=day_int)

                # Inserisco le partite estratte all'interno del dataframe
                existing_matches_pairs = { (m["HomeTeam"], m["AwayTeam"]) for m in matches }

                new_matches_data = []

                for api_match in matches_pydantic.data:
                    home_team_str = api_match.homeTeam.name 
                    away_team_str = api_match.awayTeam.name
                    match_date_str = api_match.date

                    if (home_team_str, away_team_str) not in existing_matches_pairs:
                        features = self.__dataset_editor.generate_prediction_features(
                            day=day_int,
                            home_team=home_team_str,
                            away_team=away_team_str,
                            match_date=match_date_str
                        )

                        data_oggetto = datetime.strptime(match_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                        new_matches_data.append({
                            "Date": data_oggetto.strftime("%Y-%m-%d"),
                            "HomeTeam": home_team_str,
                            "AwayTeam": away_team_str,
                            "Season": stagione_stringa,
                            "Day": day_int,
                            "Home_WinStreak": features.homeWinStreak,
                            "Away_WinStreak": features.awayWinStreak,
                            "Z_Home_Goals_Season": features.homeZGoalsSeason,
                            "Z_Home_Wins_Season": features.homeZWinsSeason,
                            "Z_Away_Goals_Season": features.awayZGoalsSeason,
                            "Z_Away_Wins_Season": features.awayZWinsSeason,
                            "GoalOnShotRatioHome": features.homeGoalOnShotRatio,
                            "GoalOnShotRatioAway": features.awayGoalOnShotRatio,
                            "HomeAdvantage": features.homeAdvantage,
                            "HomeElo": features.eloHome,
                            "AwayElo": features.eloAway,
                            "Home_Current_Points": features.pointsHome,
                            "Away_Current_Points": features.pointsAway,
                        })

                print(new_matches_data)

            except Exception as e:
                print(f"Errore durante il recupero dei match dall'API: {e}")
                matches_pydantic = None
        
        return

        partite_estratte = []
        
        if matches_pydantic and hasattr(matches_pydantic, 'data'):
            for match in matches_pydantic.data:
                squadra_casa = match.homeTeam.name    
                squadra_trasferta = match.awayTeam.name
                id_match = getattr(match, 'id', None)
                
                if self.__predictor is not None and self.__dataset_editor is not None:
                    try:
                        data_oggetto = datetime.strptime(match.date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        data_match = data_oggetto.strftime("%Y-%m-%d")
                        
                        match_features = self.__extract_match_features(
                            squadra_casa, squadra_trasferta, data_match, day_int, api_client
                        )
                        
                        features = [
                            match_features["HomeValue"] - match_features["AwayValue"],
                            match_features["Z_Home_Wins_Season"] - match_features["Z_Away_Wins_Season"],
                            abs(match_features["HomeValue"] - match_features["AwayValue"]),
                            match_features["HomeAdvantage"]
                        ]
                        
                        probabilities = self.__predictor.predict([features])
                        prediction, p1, px, p2 = self._calcola_segno_e_probabilita(probabilities)
                    except Exception as e:
                        print(f"Errore durante la predizione di {squadra_casa} vs {squadra_trasferta}: {e}")
                        prediction, p1, px, p2 = "Errore", 33, 34, 33
                else:
                    prediction, p1, px, p2 = "N/D", 33, 34, 33

                partite_estratte.append({
                    "id": id_match or f"{squadra_casa}-{squadra_trasferta}",
                    "home_team": squadra_casa,
                    "away_team": squadra_trasferta,
                    "date_match": data_match,
                    "day": day_int,
                    "prediction": prediction,
                    "prob_1": p1,
                    "prob_X": px,
                    "prob_2": p2
                })

        return render_template(
            "home.html",
            stagione_corrente=stagione_stringa,
            giornata_corrente=giornata_stringa,
            giornate_opzioni=giornate_disponibili,
            max_giornata=max_giornata,   # <-- Utile per il template
            partite=partite_estratte
        )