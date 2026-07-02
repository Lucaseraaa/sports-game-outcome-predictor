from flask.views import MethodView
from flask import render_template, request, session
from app.api.SoccerDataApi import SoccerDataApi

class HomeView(MethodView):

    def get(self):
        """
        Metodo che mostra la pagina home 
        """

        s = SoccerDataApi("1deb91e34467efc545384b5d3f0989183a8fe74c", "https://api.soccerdataapi.com", "253")
        print(s.get_season_matches("2025-2026"))

        return render_template("home.html")