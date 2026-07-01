from flask.views import MethodView
from flask import render_template

class LoginView(MethodView):

    def get(self):

        return render_template("login.html")
        