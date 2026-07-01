class SoccerDataApi:

    __api_key: str
    __base_url: str
    __league_id: str

    def __init__(self, api_key: str, base_url: str, league_id: str) -> None:
        
        self.__api_key = api_key
        self.__base_url = base_url
        self.__league_id = league_id

