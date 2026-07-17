from flask import Flask
from app.urls import import_views

app = Flask(__name__)

def main():
    """
    Funzione main: permette di avviare Flask
    """

    # Importo le route specificate
    import_views(app)
    
    app.run(debug=True) 
