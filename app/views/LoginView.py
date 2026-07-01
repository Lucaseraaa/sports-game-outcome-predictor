from flask.views import MethodView

class LoginView(MethodView):

    def get(self):

        return "Ciao, Luca"
        