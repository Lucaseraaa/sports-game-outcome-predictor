from flask.views import MethodView
from flask import render_template, request
import numpy as np

from app.api.SoccerDataApi import SoccerDataApi
from app.api.ModelPredictor import ModelPredictor  
from app.api.MatchesDatasetEditor import MatchesDatasetEditor  
from app.models.Statistics import Statistics
from app.models.Team import Team

class HomeView(MethodView):

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
            self.dataset_editor = MatchesDatasetEditor("app/static/result.csv")
        except Exception as e:
            print(f"Errore nel caricamento del MatchesDatasetEditor: {e}")
            self.dataset_editor = None

    def _estrai_4_features(self, match, match_id: int, day_int: int, api_client: SoccerDataApi) -> list:
        """
            Usa direttamente generate_prediction_features di MatchesDatasetEditor
            per calcolare le feature, estraendo poi solo quelle necessarie al Random Forest
        """
        squadra_casa = match.homeTeam.name
        squadra_trasferta = match.awayTeam.name
        
        # Gestione e pulizia della data del match
        data_match = getattr(match, 'date', '2026-01-01') 
        if "T" in data_match:
            data_match = data_match.split("T")[0]

        # Recupero del valore economico dei titolari tramite la tua SoccerDataApi
        try:
            player_stats = api_client.get_match_teams_value(match_id)
            valore_casa = player_stats.homePlayersValue
            valore_trasferta = player_stats.awayPlayersValue
        except Exception as e:
            print(f"Errore recupero valori di mercato per match {match_id}: {e}")
            valore_casa, valore_trasferta = 150_000_000, 150_000_000 

        # Calcolo di Value e Abs_Value_Difference
        value_diff = valore_casa - valore_trasferta
        abs_val_diff = abs(value_diff)

        # Creazione dell'oggetto Statistics 
        stats_match = Statistics(
            homeTeam=Team(id=int(match.homeTeam.id), name=squadra_casa),
            awayTeam=Team(id=int(match.awayTeam.id), name=squadra_trasferta),
            homeGoal=0,       # Valori fittizi necessari solo all'inizializzazione
            awayGoal=0,
            fullTimeResult='D',
            homeShots=0,
            awayShots=0,
            matchDate=data_match
        )


        features_calcolate = self.dataset_editor.generate_prediction_features(day_int, stats_match)

        # Calcolo Z_Wins_Season usando i valori restituiti da PredictionFeatures
        z_wins_season = features_calcolate.homeZWinsSeason - features_calcolate.awayZWinsSeason
        home_advantage = features_calcolate.homeAdvantage

        # Restituisco le 4 feature richieste da Random Forest
        return [value_diff, z_wins_season, abs_val_diff, home_advantage]

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

    def get(self):
        stagione_stringa = request.args.get('anno', '2025-2026')
        giornata_stringa = request.args.get('giornata', '1')
        
        giornate_disponibili = [str(i) for i in range(1, 39)]

        season_int = int(stagione_stringa.split('-')[0])
        day_int = int(giornata_stringa)

        api_client = SoccerDataApi()

        try:
            matches_pydantic = api_client.get_matches(season=season_int, day=day_int)
        except Exception as e:
            print(f"Errore durante il recupero dei match dall'API: {e}")
            matches_pydantic = None

        partite_estratte = []
        
        if matches_pydantic and hasattr(matches_pydantic, 'data'):
            for match in matches_pydantic.data:

                squadra_casa = match.homeTeam.name    
                squadra_trasferta = match.awayTeam.name
                id_match = getattr(match, 'id', None)

                if self.predictor is not None and id_match is not None and self.dataset_editor is not None:
                    try:
                        # Estrazione pulita usando generate_prediction_features
                        features = self._estrai_4_features(match, int(id_match), day_int, api_client)
                        
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