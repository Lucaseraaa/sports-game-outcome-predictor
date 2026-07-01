from app.views.LoginView import LoginView
from flask import Flask

def import_views(app: Flask) -> None:
    """
    Metodo utilizzato per importare tutte le view e associarle a degli url specifici

    Args:
        app: Istanza della classe Flask
    """

    # Importo tutte le classi View
    login_view = LoginView.as_view('user_api')

    # Gestione di tutte le routes
    app.add_url_rule('/login/', view_func=login_view, methods=['GET', ])