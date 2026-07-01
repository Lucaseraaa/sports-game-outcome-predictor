from flask.views import MethodView
from flask import render_template, request, session

class HomeView(MethodView):

    def get(self):
        """
        Metodo che mostra la pagina home 
        """

        return render_template("home.html")