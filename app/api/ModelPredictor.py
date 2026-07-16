from typing import Any

import joblib

class ModelPredictor:

    __model: Any
    __scaler: Any 

    def __init__(self, model_path: str):
        
        # Caricamento del modello
        loaded = joblib.load(model_path)
        self.__scaler = None

        # Controlla la struttura dell'oggetto caricato per estrarre modello ed eventuale scaler
        if isinstance(loaded, (tuple, list)):
            self.__model = loaded[0]
            if len(loaded) > 1:
                self.__scaler = loaded[1]
        
        elif isinstance(loaded, dict):
            self.__model = loaded.get('model')
            self.__scaler = loaded.get('scaler')
        
        else:
            self.__model = loaded
    
    def predict(self, X: list) -> Any:
        """
        Metodo che permette di effettuare una predizione a partire dalle caratteristiche del modello.
        Se lo scaler è presente nel file caricato, i dati vengono scalati prima della predizione.

        X: feature da inserire 
        """
        
        # Se lo scaler è presente, trasforma X, altrimenti usa X non modificato
        X_scaled = self.__scaler.transform(X) if self.__scaler is not None else X
        
        # Usa predict_proba() invece di predict()
        probabilities = self.__model.predict_proba(X_scaled)
        
        return probabilities
        