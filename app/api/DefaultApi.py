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

    def get(self, params: dict) -> dict:
        
        r = requests.get(self.__uri, headers=self.__headers, params=params)    

        if not r.ok:
            raise Exception(f"Messaggio ricevuto con stato {r.status_code}")

        return r.json()