from app.api.DefaultApi import DefaultApi
from app.constants import API_BASE_URL, API_TOKEN, LEAGUE_ID
from datetime import datetime
from app.models.Match import Matches

class SoccerDataApi:

    __api_key: str = API_TOKEN
    __base_url: str = API_BASE_URL
    __league_id: str = LEAGUE_ID
    __current_year: int
    __default_headers: dict

    def __init__(self) -> None:

        # Header di default
        self.__default_headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip", "x-rapidapi-key": self.__api_key}

        # Ottengo il mese e l'anno corrente, per comprendere l'anno del campionato
        today = datetime.today()
        datem = datetime(today.year, today.month, 1)
        year, month = datem.year, datem.month

        self.__current_year = year + 1 if month > 7 else year

    def get_matches(self):
        """
        Metodo che permette di estrarre tutti i prossimi match del campionato
        """
        matches_url = f"/matches"

        api = DefaultApi(
            f"{self.__base_url}{matches_url}",
            self.__default_headers,
        )

        params = {
            "leagueId": self.__league_id,
            "season": self.__current_year,
            "limit": 10, # Interessano solo le ultime 10 parite
            "offset": 10
        }

        matches = Matches.validate(api.get(params=params))
        print(matches)
        
