from flask.views import MethodView
from flask import render_template, request

class LoginView(MethodView):

    def get(self):
        """
        Metodo che mostra la pagina di login 
        """

        return render_template("login.html")
        
    def post(self):
        """
        Metodo che verifica che il login sia corretto
        """

        # Ottengo username e password
        form = request.form
        username, password = form.get("username"), form.get("password")

        # TODO: verifica username e password nel db

        return render_template("login.html")