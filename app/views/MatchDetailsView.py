from flask.views import MethodView
from flask import render_template, request
from app.constants import LINEAR_TRESHOLD, XGBOOST_TRESHOLD, FOREST_TRESHOLD

from app.api.MatchesDatasetEditor import MatchesDatasetEditor
from app.api.ModelPredictor import ModelPredictor
import numpy as np

import warnings

# Silenzia solo gli UserWarning specifici di scikit-learn relativi ai nomi delle feature
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

class MatchDetailsView(MethodView):

    def get(self, match_id):
        
        home_team = request.args.get('home', 'Squadra Casa')
        away_team = request.args.get('away', 'Squadra Trasferta')
        date_match = request.args.get('date', '')
        day = request.args.get('day', '1')
        
        # Predizioni della partita d'interesse
        dataset_editor = MatchesDatasetEditor("app/static/result.csv")
        if not dataset_editor.is_in_dataset(int(day), home_team, away_team):
            dataset_editor.add_match_in_dataset(day, home_team, away_team, date_match)
            
        # Estraggo i dati di mio interesse
        match_data = dataset_editor.extract_from_dataset(date_match, home_team, away_team)
        
        # Creo le feature per ogni modello
        linear_feature = [match_data["Home_WinStreak"] - match_data["Away_WinStreak"],
            match_data["GoalOnShotRatioHome"] - match_data["GoalOnShotRatioAway"],
            match_data["HomeElo"] - match_data["AwayElo"],
            match_data["HomeAdvantage"],
            match_data["Z_Home_Goals_Season"] - match_data["Z_Away_Goals_Season"],
            abs(match_data["Home_Current_Points"] - match_data["Away_Current_Points"])]
        
        random_forest_feature = [
            match_data["HomeValue"] - match_data["AwayValue"],
            match_data["Z_Home_Wins_Season"] - match_data["Z_Away_Wins_Season"],
            abs(match_data["HomeValue"] - match_data["AwayValue"]),
            match_data["HomeAdvantage"]
        ]

        xgboost_feature = [
            match_data["HomeValue"] - match_data["AwayValue"],
            match_data["Z_Home_Wins_Season"] - match_data["Z_Away_Wins_Season"],
            abs(match_data["HomeValue"] - match_data["AwayValue"]),
        ]

        linear_predictor = ModelPredictor("app/static/models/linear_model.joblib")
        xgboost_predictor = ModelPredictor("app/static/models/random_xgboost_model.joblib")
        forest_predictor = ModelPredictor("app/static/models/random_forest_model.joblib")

        linear_result = linear_predictor.predict([linear_feature])[0]
        xgboost_result = xgboost_predictor.predict([xgboost_feature])[0]
        forest_result = forest_predictor.predict([random_forest_feature])[0]

        prediction_linear = 1 if linear_result[1] > LINEAR_TRESHOLD else np.argmax(linear_result)
        prediction_xgbooost = 1 if xgboost_result[1] > XGBOOST_TRESHOLD else np.argmax(linear_result)
        prediction_forest = 1 if forest_result[1] > FOREST_TRESHOLD else np.argmax(linear_result)

        classes = ['1', 'X', '2']
        
        # Dati strutturati per i tuoi 3 modelli di Machine Learning
        modelli_data = [
            {
                "id": "logistic",
                "nome": "Regressione Logistica",
                "prediction": classes[int(prediction_linear)],
                "prob_1": np.round(linear_result[0]*100, 2),
                "prob_X": np.round(linear_result[1]*100, 2),
                "prob_2": np.round(linear_result[2]*100, 2),
            },
            {
                "id": "random_forest",
                "nome": "Random Forest",
                "prediction": classes[int(prediction_forest)],
                "prob_1": np.round(forest_result[0]*100, 2),
                "prob_X": np.round(forest_result[1]*100, 2),
                "prob_2": np.round(forest_result[2]*100, 2),
            },
            {
                "id": "xgboost",
                "nome": "Gradient Boosting (XGBoost)",
                "prediction": classes[int(prediction_xgbooost)],
                "prob_1": np.round(xgboost_result[0]*100, 2),
                "prob_X": np.round(xgboost_result[1]*100, 2),
                "prob_2": np.round(xgboost_result[2]*100, 2),
            }
        ]

        return render_template(
            "match_details.html",
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            modelli=modelli_data
        )