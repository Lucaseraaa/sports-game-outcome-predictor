from flask.views import MethodView
from flask import render_template, request

class MatchDetailsView(MethodView):

    def get(self, match_id):

        
        home_team = request.args.get('home', 'Squadra Casa')
        away_team = request.args.get('away', 'Squadra Trasferta')

        # Dati strutturati per i tuoi 3 modelli di Machine Learning
        modelli_data = [
            {
                "id": "logistic",
                "nome": "Regressione Logistica",
                "prediction": "1",
                "prob_1": 52,
                "prob_X": 28,
                "prob_2": 20,
            },
            {
                "id": "random_forest",
                "nome": "Random Forest",
                "prediction": "1X",
                "prob_1": 45,
                "prob_X": 35,
                "prob_2": 20,
            },
            {
                "id": "xgboost",
                "nome": "Gradient Boosting (XGBoost)",
                "prediction": "1",
                "prob_1": 58,
                "prob_X": 24,
                "prob_2": 18,
            }
        ]

        return render_template(
            "match_details.html",
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            modelli=modelli_data
        )