from app.api.DefaultApi import DefaultApi
from app.constants import API_BASE_URL, API_TOKEN, LEAGUE_ID
from datetime import datetime
from app.models.Match import Matches
from app.models.Statistics import Statistics
from app.models.Team import Team
from app.models.PlayerStatistics import PlayerStatistics

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

    def get_matches(self) -> Matches:
        """
        Metodo che permette di estrarre tutti i prossimi match del campionato

        Return:
            lista di match d'interesse

        Raises
            ValidationError: errore di validazione della richiesta API
            RequesException: errore stato non ok
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

        return Matches.model_validate(api.get(params=params))
        
        
    def get_match_detail(self, match_id: int) -> Statistics:
        """
        Metodo che permette di visualizzare i dettagli del match specificato

        Args:
            match_id: id del match da interrogare

        Returns:
            homeTeam: squadra in casa
            awayTeam: squadra in trasferta
            homeGoal: goal della squadra di casa
            awayGoal: goal della squadra di trasferta
            fullTimeResult: risultato finale (H, D, A)
            homeShots: tiri in porta in casa
            awayShots: tiri in porta in trasferta

        """
        match_url = f"/matches/{match_id}"

        api = DefaultApi(
            f"{self.__base_url}{match_url}",
            self.__default_headers,
        )

        # Ottengo le statistiche che mi interessano
        json_result = api.get(params={})[0]

        goals = json_result.get("state").get("score").get("current").split(" - ")
        goals_home, goals_away = int(goals[0]), int(goals[1])

        statistics = json_result.get("statistics")
        home_statistics, away_statistics = statistics[0].get('statistics'), statistics[1].get('statistics')
        print(f"Statistic: {home_statistics}")
        home_shot_on_target, away_shot_on_target = home_statistics[27].get('value'), away_statistics[27].get('value')

        home_team = Team(
            id=int(json_result.get("homeTeam").get("id")),
            name=json_result.get("homeTeam").get("name")
        )

        away_team = Team(
            id=int(json_result.get("awayTeam").get("id")),
            name=json_result.get("awayTeam").get("name")
        )

        return Statistics(
            homeTeam=home_team,
            awayTeam=away_team,
            homeGoal=goals_home,
            awayGoal=goals_away,
            fullTimeResult='H' if goals_home > goals_away else ('D' if goals_home == goals_away else 'A'),
            homeShots=home_shot_on_target,
            awayShots=away_shot_on_target
        )
    
    def get_match_teams_value(self, match_id: int) -> PlayerStatistics:
        """
        Metodo che permette di ottenere il valore della rosa delle squadre di una partita

        Args: 
            match_id: id della partita selezionata

        Returns:
            lista dei giocatori titolari della partita
        """

        match_url = f"/box-score/{match_id}"

        api = DefaultApi(
            f"{self.__base_url}{match_url}",
            self.__default_headers,
        )

        # Ottengo le statistiche che mi interessano
        json_result = api.get(params={})
        # print(json_result)

        home_players, away_players = json_result[0].get("players"), json_result[1].get("players")
        print(home_players)

        # Labmda che mi prende i giocatori titolari
        get_starting_players = lambda players: [player["fullName"] for player in players if player.get("isSubstitute") is False]

        starters_home, starters_away = get_starting_players(home_players), get_starting_players(away_players)

        return PlayerStatistics(
            homePlayers=starters_home,
            awayPlayers=starters_away
        )