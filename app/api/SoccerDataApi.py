from app.api.DefaultApi import DefaultApi
from app.constants import API_BASE_URL, API_TOKEN, LEAGUE_ID
from datetime import datetime
from app.models.Match import Matches
from app.models.Statistics import Statistics
from app.models.Team import Team
from app.models.PlayerStatistics import PlayerStatistics
from app.api.MatchesDatasetEditor import MatchesDatasetEditor
from app.api.PlayerHepler import PlayerHelper

# Casi speciali
special = {
    "AC Milan": "Milan",
    "AS Roma": "Roma"
}

class SoccerDataApi:

    __api_key: str = API_TOKEN
    __base_url: str = API_BASE_URL
    __league_id: str = LEAGUE_ID
    __default_headers: dict

    def __init__(self) -> None:

        # Header di default
        self.__default_headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip", "x-rapidapi-key": self.__api_key}

    def get_matches(self, season: int, day: int) -> Matches:
        """
        Metodo che permette di estrarre tutti i prossimi match del campionato

        Args:
            season: stagione del campionato (inserire la prima nell'AA-20XX-20YY)
            day: giornata (da 1 a 38)

        Returns:
            lista di match d'interesse

        Raises:
            ValidationError: errore di validazione della richiesta API
            RequesException: errore stato non ok
        """
        matches_url = f"/matches"

        api = DefaultApi(
            f"{self.__base_url}{matches_url}",
            self.__default_headers,
        )

        # Prima chiamata per ottenere il numero di partite presenti
        info_params = {
            "leagueId": self.__league_id,
            "season": season,
            "limit": 1,
            "offset": 500
        }

        info_request = api.get(params=info_params)
        total_count = int(info_request.get("pagination").get("totalCount"))

        # Invio richieste fino ad arrivare alle partite che mi interessano
        # Per la giornata devo scegliere l'offset opposto alla partita
        day_offset = (int(total_count/10) - day) * 10

        # Ci interessano solo 10 partite 
        params = {
            "leagueId": self.__league_id,
            "season": season,
            "limit": 10, # Interessano solo le ultime 10 parite
            "offset": day_offset
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
        print(json_result)
        goals = json_result.get("state").get("score").get("current").split(" - ")
        goals_home, goals_away = int(goals[0]), int(goals[1])
        date = datetime.strptime(json_result.get("date"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")

        statistics = json_result.get("statistics")
        home_statistics, away_statistics = statistics[0].get('statistics'), statistics[1].get('statistics')
        print(f"Statistic: {home_statistics}")
        home_shot_on_target, away_shot_on_target = home_statistics[27].get('value'), away_statistics[27].get('value')

        home_team = Team(
            id=int(json_result.get("homeTeam").get("id")),
            name=special[json_result.get("homeTeam").get("name")] if json_result.get("homeTeam").get("name") in special else json_result.get("homeTeam").get("name") 
        )

        away_team = Team(
            id=int(json_result.get("awayTeam").get("id")),
            name=special[json_result.get("awayTeam").get("name")] if json_result.get("awayTeam").get("name") in special else json_result.get("awayTeam").get("name") 
        )

        s = Statistics(
            homeTeam=home_team,
            awayTeam=away_team,
            homeGoal=goals_home,
            awayGoal=goals_away,
            fullTimeResult='H' if goals_home > goals_away else ('D' if goals_home == goals_away else 'A'),
            homeShots=home_shot_on_target,
            awayShots=away_shot_on_target,
            matchDate=date
        )

        md = MatchesDatasetEditor("app/static/result.csv")
        md.add_in_dataset(1, s)
        return s
    
    def get_match_teams_value(self, match_id: int) -> PlayerStatistics:
        """
        Metodo che permette di ottenere il valore della rosa delle squadre di una partita

        Args: 
            match_id: id della partita selezionata

        Returns:
            costi delle rose delle squadre
        """

        match_url = f"/box-score/{match_id}"

        api = DefaultApi(
            f"{self.__base_url}{match_url}",
            self.__default_headers,
        )

        # Ottengo le statistiche che mi interessano
        json_result = api.get(params={})

        home_players, away_players = json_result[0].get("players"), json_result[1].get("players")

        # Labmda che mi prende il costo dei titolari
        helper = PlayerHelper("app/static/market-values.csv")
        get_starting_players_values = lambda players: sum(
            helper.get_player_market_value(player["fullName"]) 
            for player in players if player.get("isSubstitute") is False
        )
        starters_home, starters_away = get_starting_players_values(home_players), get_starting_players_values(away_players)
        
        return PlayerStatistics(
            homePlayersValue=starters_home,
            awayPlayersValue=starters_away
        )