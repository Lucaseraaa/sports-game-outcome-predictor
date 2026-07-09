import pandas as pd
from app.models.Statistics import Statistics

# Casi particolari


class MatchesDatasetEditor:

    __dataset: pd.DataFrame

    def __init__(
        self,
        dataset_path: str
    ) -> None:

        # Caricamento del dataset
        raw_dataset = pd.read_csv(dataset_path)

        self.__dataset = raw_dataset.set_index(["Date", "HomeTeam", "AwayTeam"])
        self.__dataset = self.__dataset.sort_index()
    
    def is_in_dataset(self, date: str, home_team: str, away_team: str) -> bool:
        """
        Metodo che permette di verificare se un record (data + squadra casa + squadra trasferta) è già presente nel dataset

        Args:
            date: data della partita (in formato AAAA-MM-DD)
            home_team: squadra di casa
            away_team: squadra in trasferta

        Returns:
            ritorna un booleano che indica se la condizione è stata verificata
        """

        try:
            self.__dataset.loc[(date, home_team, away_team)]
        
        except KeyError:
            
            return False # Non esiste il record

        return True 
    
    def __get_winstreak(self, team: str, match_date: str, day: int) -> int:
        """
        Metodo utilizzato per calcolare il winstreak di una squadra all'interno del campionato

        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            winstreak della squadra
        """
        # Se è la prima giornata, la striscia è per forza 0
        if day == 1:
            return 0

        # Determiniamo l'inizio della stagione (da agosto in poi)
        year = int(match_date[:4])
        month = int(match_date[5:7])
        
        season_start_year = year if month > 7 else year - 1
        season_start = f"{season_start_year}-08-01"

        df = self.__dataset.reset_index()

        is_playing = (df["HomeTeam"] == team) | (df["AwayTeam"] == team)
        is_current_season_past = (df["Date"] >= season_start) & (df["Date"] < match_date)
        past_matches = df[is_playing & is_current_season_past].sort_values(by="Date", ascending=False)

        winstreak = 0

        # Calcolo della streak
        for _, match in past_matches.iterrows():
            won_home = (match["HomeTeam"] == team) and (match["FTR"] == "H")
            won_away = (match["AwayTeam"] == team) and (match["FTR"] == "A")

            if won_home or won_away:
                winstreak += 1
            else:
                break

        return winstreak

    def __get_goal_on_shot_ratio(self, team: str, match_date: str, day: int) -> float:
        """
        Metodo utilizzato per calcolare il rapporto tra goal e tiri in porta 
        di una squadra nelle ultime partite (max 5) della stagione in corso.

        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            Rapporto Goal / Tiri in porta (float). Ritorna 0.0 in caso di prima giornata
            o se la squadra non ha effettuato tiri in porta.
        """
        # Caso limite: prima giornata
        if day == 1:
            return 0.0

        # Inizio della stagione
        year = int(match_date[:4])
        month = int(match_date[5:7])
        
        season_start_year = year if month > 7 else year - 1
        season_start = f"{season_start_year}-08-01"

        df = self.__dataset.reset_index()
        is_playing = (df["HomeTeam"] == team) | (df["AwayTeam"] == team)
        is_current_season_past = (df["Date"] >= season_start) & (df["Date"] < match_date)
        
        # Ricerca
        past_matches = df[is_playing & is_current_season_past].sort_values(by="Date", ascending=False).head(5)

        if past_matches.empty:
            return 0.0

        total_goals = 0
        total_shots_on_target = 0

        # Calcolo della somma dei goal
        for _, match in past_matches.iterrows():
            if match["HomeTeam"] == team:
                total_goals += match["FTHG"]
                total_shots_on_target += match.get("HST", 0) 
            else:
                total_goals += match["FTAG"]
                total_shots_on_target += match.get("AST", 0)

        # Prevenzione divisione per 0
        if total_shots_on_target == 0:
            return 0.0

        return total_goals / total_shots_on_target


    def __get_point_to_match_ratio(self, team: str, match_date: str, day: int) -> float:
        """
        Metodo utilizzato per calcolare il rapporto tra vittorie e partite disputate 
        nelle ultime partite (max 5) della stagione in corso.

        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            Rapporto Vittorie / Partite disputate (float). 
            Ritorna 0.0 in caso di prima giornata o se non ci sono partite precedenti.
        """
        # Caso limite
        if day == 1:
            return 0.0

        year = int(match_date[:4])
        month = int(match_date[5:7])
        
        season_start_year = year if month > 7 else year - 1
        season_start = f"{season_start_year}-08-01"

        
        df = self.__dataset.reset_index()
        is_playing = (df["HomeTeam"] == team) | (df["AwayTeam"] == team)
        is_current_season_past = (df["Date"] >= season_start) & (df["Date"] < match_date)
        

        past_matches = df[is_playing & is_current_season_past].sort_values(by="Date", ascending=False).head(5)
        total_matches = len(past_matches)

        if total_matches == 0:
            return 0.0

        wins = 0
        for _, match in past_matches.iterrows():
            won_home = (match["HomeTeam"] == team) and (match["FTR"] == "H")
            won_away = (match["AwayTeam"] == team) and (match["FTR"] == "A")

            if won_home or won_away:
                wins += 1

        return wins / total_matches

    def add_in_dataset(self, day: int, statistics: Statistics) -> bool:
        """
        Metodo che permette di inserire un record (data + squadra casa + squadra trasferta) nel dataset

        Args:
            day: giornata di campionato
            statistics: statistiche della partita

        Returns:
            ritorna un booleano che indica il risultato dell'operazione
        """

        date, home_team, away_team = statistics.matchDate, statistics.homeTeam.name, statistics.awayTeam.name

        # Controllo che il record non esista già
        #if self.is_in_dataset(date, home_team, away_team):
        #    return False

        # Inserisco il record (con tutti i dati che servono)
        baseline = [date, home_team, away_team, statistics.homeGoal, statistics.awayGoal, statistics.fullTimeResult]

        # Calcolo corretto della season
        sep_date = date.split('-')
        year, month = int(sep_date[0]), int(sep_date[1])
        
        # Se siamo tra agosto e dicembre, l'anno di inizio è l'anno corrente.
        # Se siamo tra gennaio e luglio, l'anno di inizio è l'anno precedente.
        start_year = year if month > 7 else year - 1

        baseline.append(f"{start_year}-{start_year+1}")

        # Aggiunta della winstreak passando il parametro day
        baseline.append(self.__get_winstreak(statistics.homeTeam.name, statistics.matchDate, day))
        baseline.append(self.__get_winstreak(statistics.awayTeam.name, statistics.matchDate, day))

        # Aggiunta del GoalOnShotRatio
        baseline.append(self.__get_goal_on_shot_ratio(statistics.homeTeam.name, statistics.matchDate, day))
        baseline.append(self.__get_goal_on_shot_ratio(statistics.awayTeam.name, statistics.matchDate, day))

        # Aggiunta del PointToMatchRatio
        baseline.append(self.__get_point_to_match_ratio(statistics.homeTeam.name, statistics.matchDate, day))
        baseline.append(self.__get_point_to_match_ratio(statistics.awayTeam.name, statistics.matchDate, day))

        print(baseline)
        
        return True 
        