from app.views.MatchDetailsView import MatchDetailsView
from app.views.HomeView import HomeView
from app.views.BetView import BetView
from flask import Flask

def import_views(app: Flask) -> None:
    """
    Metodo utilizzato per importare tutte le view e associarle a degli url specifici

    Args:
        app: Istanza della classe Flask
    """

    # Importo tutte le classi View
    home_view = HomeView.as_view('home')
    bet_view = BetView.as_view('bet')

    # Gestione di tutte le routes
    app.add_url_rule('/', view_func=home_view, methods=['GET', ])
    app.add_url_rule('/bet/', view_func=bet_view, methods=['GET', ])
    app.add_url_rule('/match/<string:match_id>', view_func=MatchDetailsView.as_view('match_details')
    )   