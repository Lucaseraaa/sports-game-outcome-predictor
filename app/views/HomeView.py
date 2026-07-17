from datetime import datetime
import time

from flask.views import MethodView
from flask import render_template, request
import numpy as np

from app.api.SoccerDataApi import SoccerDataApi
from app.api.ModelPredictor import ModelPredictor  
from app.api.MatchesDatasetEditor import MatchesDatasetEditor  
from app.models.Statistics import Statistics
from app.models.Team import Team

class HomeView(MethodView):

    __dataset_editor: MatchesDatasetEditor

    def __init__(self):
        super().__init__()
        
        # Caricamento del modello Random Forest
        try:
            self.predictor = ModelPredictor("app/static/models/random_forest_model.joblib")
        except Exception as e:
            print(f"Errore nel caricamento del modello Random Forest: {e}")
            self.predictor = None

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

    def __extract_match_features(self, home_team: str, away_team: str, match_day: str, day: int):
        """
        Metodo utilizzato per poplare ed estrarre i dati dal dataframe
        """

        if not self.__dataset_editor.is_in_dataset(match_day, home_team, away_team):
            self.__dataset_editor.add_match_in_dataset(day, home_team, away_team, match_day)
            
        # Estraggo i dati di mio interesse
        return self.__dataset_editor.extract_from_dataset(match_day, home_team, away_team)
        


    def get(self):
        stagione_stringa = request.args.get('anno', '2025-2026')
        giornata_stringa = request.args.get('giornata', '1')
        
        giornate_disponibili = [str(i) for i in range(1, 39)]

        season_int = int(stagione_stringa.split('-')[0])
        day_int = int(giornata_stringa)

        api_client = SoccerDataApi()
        
        try:
            matches_pydantic = api_client.get_matches(season=season_int, day=day_int)
            print("Match ottenuti: ", matches_pydantic)
        except Exception as e:
            
            print(f"Errore durante il recupero dei match dall'API: {e}")
            matches_pydantic = None

        partite_estratte = []
        
        if matches_pydantic and hasattr(matches_pydantic, 'data'):
            for match in matches_pydantic.data:
    
                # Definisco i dati delle partite
                squadra_casa = match.homeTeam.name    
                squadra_trasferta = match.awayTeam.name
                id_match = getattr(match, 'id', None)

                if self.predictor is not None and self.__dataset_editor is not None:
                    try:

                        # Popolamento del dataset con i dati delle partite d'interesse
                        data_oggetto = datetime.strptime(match.date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        data_match = data_oggetto.strftime("%Y-%m-%d")
                        match_features = self.__extract_match_features(squadra_casa, squadra_trasferta, data_match, day_int)
                        
                        # Recupero le features di mio interesse per il random forest
                        features = [match_features["HomeValue"] - match_features["AwayValue"], match_features["Z_Home_Wins_Season"] - match_features["Z_Away_Wins_Season"], abs(match_features["HomeValue"] - match_features["AwayValue"]), match_features["HomeAdvantage"]]

                        # Predizione tramite Random Forest
                        probabilities = self.predictor.predict([features])
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
            partite=partite_estratte
        )