import requests

class DefaultApi:

    __uri: str
    __method: str
    __headers: dict
    __body: dict 

    def __init__(self, uri: str, headers: dict, body: dict) -> None:
        
        self.__uri = uri
        self.__headers = headers
        self.__body = body
    
    def __modify_url(self, params: dict) -> None:
        
        for key, value in params.values():
            append_uri += f"?{key}={value}" 


    def get(self, params: dict) -> dict:

        try:
            
            self.__modify_url(params) # Modifico l'uri con i parametri d'interesse
            r = requests.get(self.__uri, headers=self.__headers)

        except Exception as e:

            print(f"Errore nella richiesta: {e}")

        if not r.ok:
            raise Exception(f"Messaggio ricevuto con stato {r.status_code}")

        return r.json()