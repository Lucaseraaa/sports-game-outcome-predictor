from flask.views import MethodView
from flask import render_template, request, session
from app.api.SoccerDataApi import SoccerDataApi

class HomeView(MethodView):

    def get(self):
        """
        Metodo che mostra la pagina home 
        """

        s = SoccerDataApi()
        s.get_match_teams_value(1172882173)

        return render_template("home.html")