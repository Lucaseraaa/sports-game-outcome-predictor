from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Ciao, Flask!"

def main():
    """
    Funzione main: permette di avviare Flask
    """
    
    app.run(debug=True) 
