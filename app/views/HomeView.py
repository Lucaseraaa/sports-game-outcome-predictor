from flask.views import MethodView
from flask import render_template, request, session
from app.api.PlayerHepler import PlayerHelper
from app.api.SoccerDataApi import SoccerDataApi

class HomeView(MethodView):

    def get(self):
        """
        Metodo che mostra la pagina home 
        """
        
        #p = PlayerHelper("app/static/market-values.csv")
        #print(type(p.get_player_market_value("Marcus Thuram")))

        s = SoccerDataApi()
        s.get_match_teams_value(1172882173)

        return render_template("home.html")