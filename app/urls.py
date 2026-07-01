from app.views.LoginView import LoginView
from app.views.HomeView import HomeView
from flask import Flask

def import_views(app: Flask) -> None:
    """
    Metodo utilizzato per importare tutte le view e associarle a degli url specifici

    Args:
        app: Istanza della classe Flask
    """

    # Importo tutte le classi View
    login_view = LoginView.as_view('login')
    home_view = HomeView.as_view('home')

    # Gestione di tutte le routes
    app.add_url_rule('/login/', view_func=login_view, methods=['GET', 'POST'])
    app.add_url_rule('/', view_func=home_view, methods=['GET', ])