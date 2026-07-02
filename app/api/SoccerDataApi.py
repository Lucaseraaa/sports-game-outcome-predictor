from app.api.DefaultApi import DefaultApi

class SoccerDataApi:

    __api_key: str
    __base_url: str
    __league_id: str
    __default_headers: dict

    def __init__(self, api_key: str, base_url: str, league_id: str) -> None:
        
        self.__api_key = api_key
        self.__base_url = base_url
        self.__league_id = league_id
        self.__default_headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}

    def get_season_matches(self, season: str) -> dict:
        """
        Metodo che ritorna tutte le partite del campionato in una stagione specificata

        Args:
            season: stagione del campionato, da inserire nel formato aaaa-bbbb

        Return:
            dizionario contenente tutte le partite del campionato specificato
        """

        params = {
            "season": season,
            "league_id": self.__league_id,
            "auth_token": self.__api_key
        }

        api = DefaultApi(
            f"{self.__base_url}/matches",
            self.__default_headers,
            {}
        )

        return api.get(params=params)