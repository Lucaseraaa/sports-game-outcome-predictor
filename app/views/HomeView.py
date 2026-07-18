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

    def __get_probs(self, probabilities) -> tuple:
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

    def __get_available_day(self, stagione_stringa: int) -> list[int]:
        """
        Metodo che permette di estrarre le giornate che possono essere visualizzate

        Args:
            stagione_stringa: stringa che indica la stagione corrente

        Returns: 
            lista delle giornate disponibili
        """

        season_int = int(stagione_stringa.split('-')[0])
        oggi = datetime.now().date()
        
        is_current_season = (season_int == oggi.year) or (season_int + 1 == oggi.year)
        
        if is_current_season:
            max_giornata = 1 
            
            for d in range(1, 38):
                
                matches_d = self.__dataset_editor.get_all_match_of_day(stagione_stringa, d)
        
                if not matches_d:
                    break
                    
                # Estraggo la data dell'ultima partita giocata nella giornata 'd'
                max_date_str = max([m["Date"] for m in matches_d])
                max_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
                
                if oggi > max_date:
                    max_giornata = d + 1
                else:
                    break 
            
            return [str(i) for i in range(1, max_giornata + 1)]
        else:

            # Se è una stagione passata, le partite sono già tutte giocate: sblocco tutto
            return [str(i) for i in range(1, 39)]


    
    def get(self):
        from datetime import datetime
    
        stagione_stringa = request.args.get('anno', '2026-2027')
        giornata_stringa = request.args.get('giornata', '1')
        
        season_int = int(stagione_stringa.split('-')[0])
        requested_day = int(giornata_stringa)
        
        api_client = SoccerDataApi()
        
        day_int = requested_day
        
        giornate_disponibili = self.__get_available_day(stagione_stringa)

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
                            "HomeValue": 0,
                            "AwayValue": 0,
                            "PointToMatchRatioHome": features.homePointToMatchRatio, # Aggiunto
                            "PointToMatchRatioAway": features.awayPointToMatchRatio, # Aggiunto
                        })

                if new_matches_data:
                    
                    # Inserimento delle partite nel dataframe
                    self.__dataset_editor.add_new_matches(new_matches_data)
                    
                    # Merge dei due array
                    matches = matches + new_matches_data

            except Exception as e:
                print(f"Errore durante il recupero dei match dall'API: {e}")
                matches_pydantic = None
        

        partite_estratte = []
        
        for match in matches:
            # Estraiamo i dati di base dal dizionario del match
            squadra_casa = match["HomeTeam"]
            squadra_trasferta = match["AwayTeam"]
            data_match = match["Date"]
            
            # Gestiamo l'ID del match se non è presente nel dizionario del dataset
            id_match = match.get("id") or f"{squadra_casa}-{squadra_trasferta}"
            
            if self.__predictor is not None and self.__dataset_editor is not None:
                try:
        
                    home_value = match.get("HomeValue") or 0.0
                    away_value = match.get("AwayValue") or 0.0
                    
                    z_home_wins = match.get("Z_Home_Wins_Season") or 0.0
                    z_away_wins = match.get("Z_Away_Wins_Season") or 0.0
                    
                    home_advantage = match.get("HomeAdvantage") or 0.0
                    
                    # Costruiamo l'array delle feature per il modello
                    features = [
                        home_value - away_value,
                        z_home_wins - z_away_wins,
                        abs(home_value - away_value),
                        home_advantage
                    ]
                    
                    # Eseguiamo la predizione
                    probabilities = self.__predictor.predict([features])
                    prediction, p1, px, p2 = self.__get_probs(probabilities)
                    
                except Exception as e:
                    print(f"Errore durante la predizione di {squadra_casa} vs {squadra_trasferta}: {e}")
                    prediction, p1, px, p2 = "Errore", 33, 34, 33
            else:
                prediction, p1, px, p2 = "N/D", 33, 34, 33

            # Aggiungiamo il match elaborato alla lista per il template HTML
            partite_estratte.append({
                "id": id_match,
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
            giornata_corrente=str(day_int), 
            giornate_opzioni=giornate_disponibili,
            max_giornata=38,   
            partite=partite_estratte
        )