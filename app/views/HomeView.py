from flask.views import MethodView
from flask import render_template, request
from app.api.SoccerDataApi import SoccerDataApi

class HomeView(MethodView):

    def get(self):

        # 1. Recuperiamo i valori stringa inviati dal form HTML (con i default di fallback)
        stagione_stringa = request.args.get('anno', '2025-2026')
        giornata_stringa = request.args.get('giornata', '1')
        
        # Genero le 38 giornate per il menu a tendina
        giornate_disponibili = [str(i) for i in range(1, 39)]

        # Conversione per l'API, trasformo le stringhe in interi
        season_int = int(stagione_stringa.split('-')[0])
        day_int = int(giornata_stringa)

        # Istazio il client API
        api_client = SoccerDataApi()

        # Chiamo il metodo get_matches gestendo eventuali errori 
        try:
            matches_pydantic = api_client.get_matches(season=season_int, day=day_int)
        except Exception as e:
            print(f"Errore durante il recupero dei match dall'API: {e}")
            matches_pydantic = None


        partite_estratte = []
        
        if matches_pydantic and hasattr(matches_pydantic, 'data'):
            for match in matches_pydantic.data:

                # Accediamo alle proprietà del singolo match 
                squadra_casa = match.homeTeam.name    
                squadra_trasferta = match.awayTeam.name

                # AGGIUNGERE PREDICTION QUA ---------------------------------------------
                prediction = "1X"
                p1, px, p2 = 45, 35, 20

                partite_estratte.append({
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
    
