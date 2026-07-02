from flask.views import MethodView
from flask import render_template, request, session
from app.api.SoccerDataApi import SoccerDataApi

class HomeView(MethodView):

    def get(self):
        """
        Metodo che mostra la pagina home 
        """

        s = SoccerDataApi()
        s.get_matches()

        return render_template("home.html")