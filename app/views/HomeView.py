from flask.views import MethodView
from flask import render_template, request, session
from app.api.PlayerHepler import PlayerHelper
from app.api.SoccerDataApi import SoccerDataApi

class HomeView(MethodView):

    def get(self):
        """
        Metodo che mostra la pagina home con filtri dinamici per stagione e giornata.
        """
        
        #p = PlayerHelper("app/static/market-values.csv")
        #print(type(p.get_player_market_value("Marcus Thuram")))

        # Recuperiamo i filtri dall'URL. Se non ci sono, impostiamo i valori di default.
        stagione_selezionata = request.args.get('anno', '2025-2026')
        giornata_selezionata = request.args.get('giornata', '1')

        # Logica in Python per decidere quali giornate mostrare nella tendina
        if stagione_selezionata == '2025-2026':
            # Genera le 38 giornate
            giornate_disponibili = [str(i) for i in range(1, 39)]
        else:
            # Per la nuova stagione 2026-2027 permette solo il turno Live futuro
            giornate_disponibili = ['Prossima Giornata']
            giornata_selezionata = 'Prossima Giornata'

        # 3. QUI in futuro userai la tua SoccerDataApi o i tuoi modelli per estrarre i match reali
        # es: partite = SoccerDataApi.get_matches(stagione_selezionata, giornata_selezionata)
        partite_estratte = [] 

        # Passiamo tutte le variabili calcolate da Python a Jinja
        return render_template(
            "home.html",
            stagione_corrente=stagione_selezionata,
            giornata_corrente=giornata_selezionata,
            giornate_opzioni=giornate_disponibili,
            partite=partite_estratte
        )