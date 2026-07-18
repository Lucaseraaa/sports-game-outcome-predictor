import requests
from requests.exceptions import RequestException

class DefaultApi:

    __uri: str
    __headers: dict

    def __init__(self, uri: str, headers: dict) -> None:
        
        self.__uri = uri
        self.__headers = headers

    def get(self, params: dict) -> dict:
        """
        Metodo che permette di effettuare una chiamata GET agli api

        Args:
            params: parametri da passare all'endpoint

        Return:
            risposta del server in formato dict
        """

        r = requests.get(self.__uri, headers=self.__headers, params=params)    
        
        if not r.ok:
            raise RequestException(f"Messaggio ricevuto con stato {r.status_code}")

        return r.json()