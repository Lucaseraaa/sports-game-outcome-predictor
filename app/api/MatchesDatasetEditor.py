import pandas as pd
from app.models.Statistics import Statistics
from app.models.PredictionFeatures import PredictionFeatures


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

    def __get_home_advantage(self, team: str, match_date: str, day: int) -> float:
        """
        Metodo utilizzato per calcolare l'Home Advantage, ovvero il rapporto tra 
        vittorie in casa e partite giocate in casa nelle ultime (max 5) della stagione in corso.

        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            Rapporto Vittorie in casa / Partite in casa disputate (float).
            Ritorna 0.0 in caso di prima giornata o se non ci sono partite in casa precedenti.
        """

        # Caso limite
        if day == 1:
            return 0.0

        year = int(match_date[:4])
        month = int(match_date[5:7])
        
        season_start_year = year if month > 7 else year - 1
        season_start = f"{season_start_year}-08-01"

        df = self.__dataset.reset_index()

        is_playing_home = (df["HomeTeam"] == team)
        is_current_season_past = (df["Date"] >= season_start) & (df["Date"] < match_date)
        
        past_home_matches = df[is_playing_home & is_current_season_past].sort_values(by="Date", ascending=False).head(5)
        total_home_matches = len(past_home_matches)

        if total_home_matches == 0:
            return 0.0

        home_wins = 0
        for _, match in past_home_matches.iterrows():
            if match["FTR"] == "H":
                home_wins += 1

        return home_wins / total_home_matches
    
    def __get_z_goals(self, team: str, match_date: str, day: int) -> float:
        """
        Calcola lo Z-score dei goal fatti dalla squadra rispetto al resto della lega,
        prendendo in considerazione le partite della stagione giocate fino a quel momento.
        
        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            Valore Z-Score per i goal (float). Ritorna 0.0 in caso di prima giornata o deviazione nulla.
        """
        # Caso limite
        if day <= 1:
            return 0.0
            
        year = int(match_date[:4])
        month = int(match_date[5:7])
        season_start_year = year if month > 7 else year - 1
        season_start = f"{season_start_year}-08-01"

        df = self.__dataset.reset_index()

        is_current_season_past = (df["Date"] >= season_start) & (df["Date"] < match_date)
        past_matches = df[is_current_season_past]

        if past_matches.empty:
            return 0.0

        home_goals = past_matches[["HomeTeam", "FTHG"]].rename(columns={"HomeTeam": "Team", "FTHG": "Goals"})
        away_goals = past_matches[["AwayTeam", "FTAG"]].rename(columns={"AwayTeam": "Team", "FTAG": "Goals"})
        
        all_goals = pd.concat([home_goals, away_goals])

        team_avg_goals = all_goals.groupby("Team")["Goals"].mean()
        team_avg = team_avg_goals.get(team, 0.0)

        league_mean = team_avg_goals.mean()
        league_std = team_avg_goals.std() 

        if pd.isna(league_std) or league_std == 0.0:
            return 0.0

        return (team_avg - league_mean) / league_std
    
    def __get_z_wins(self, team: str, match_date: str, day: int) -> float:
        """
        Calcola lo Z-score delle vittorie della squadra rispetto al resto della lega,
        prendendo in considerazione le partite della stagione giocate fino a quel momento.
        
        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            Valore Z-Score per le vittorie (float). Ritorna 0.0 in caso di prima giornata o deviazione nulla.
        """
        
        # Caso limite
        if day <= 1:
            return 0.0
            
        year = int(match_date[:4])
        month = int(match_date[5:7])
        season_start_year = year if month > 7 else year - 1
        season_start = f"{season_start_year}-08-01"

        df = self.__dataset.reset_index()

        is_current_season_past = (df["Date"] >= season_start) & (df["Date"] < match_date)
        past_matches = df[is_current_season_past]

        if past_matches.empty:
            return 0.0

        home_wins = past_matches[["HomeTeam", "FTR"]].rename(columns={"HomeTeam": "Team"})
        home_wins["Win"] = (home_wins["FTR"] == "H").astype(int)
        
        away_wins = past_matches[["AwayTeam", "FTR"]].rename(columns={"AwayTeam": "Team"})
        away_wins["Win"] = (away_wins["FTR"] == "A").astype(int)
        
        all_wins = pd.concat([home_wins[["Team", "Win"]], away_wins[["Team", "Win"]]])

        team_avg_wins = all_wins.groupby("Team")["Win"].mean()

        team_avg = team_avg_wins.get(team, 0.0)

        league_mean = team_avg_wins.mean()
        league_std = team_avg_wins.std()

        if pd.isna(league_std) or league_std == 0.0:
            return 0.0

        return (team_avg - league_mean) / league_std

    def generate_prediction_features(self, day: int, statistics: Statistics) -> PredictionFeatures:
        """
        Metodo utilizzato per generare le feature necessarie per la predizione 
        Args:
            day: giornata di campionato
            statistics: statistiche della partita
        
        Returns:
            istanza della classe che indica i valori necessari alle previsioni
        """

        return PredictionFeatures(
            homeWinStreak=self.__get_winstreak(statistics.homeTeam.name, statistics.matchDate, day),
            awayWinStreak=self.__get_winstreak(statistics.awayTeam.name, statistics.matchDate, day),
            homeGoalOnShotRatio=self.__get_goal_on_shot_ratio(statistics.homeTeam.name, statistics.matchDate, day),
            awayGoalOnShotRatio=self.__get_goal_on_shot_ratio(statistics.awayTeam.name, statistics.matchDate, day),
            homePointToMatchRatio=self.__get_point_to_match_ratio(statistics.homeTeam.name, statistics.matchDate, day),
            awayPointToMatchRatio=self.__get_point_to_match_ratio(statistics.awayTeam.name, statistics.matchDate, day),
            homeAdvantage=self.__get_home_advantage(statistics.homeTeam.name, statistics.matchDate, day),
            homeZGoalsSeason=self.__get_z_goals(statistics.homeTeam.name, statistics.matchDate, day),
            awayZGoalsSeason=self.__get_z_goals(statistics.awayTeam.name, statistics.matchDate, day),
            homeZWinsSeason=self.__get_z_wins(statistics.homeTeam.name, statistics.matchDate, day),
            awayZWinsSeason=self.__get_z_wins(statistics.awayTeam.name, statistics.matchDate, day)
        )


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

        # Ottengo le feature di predizione e le unisco
        features = self.generate_prediction_features(day, statistics)

        baseline += [
            features.homeWinStreak,
            features.awayWinStreak,
            features.homeGoalOnShotRatio,
            features.awayGoalOnShotRatio,
            features.homePointToMatchRatio,
            features.awayPointToMatchRatio,
            features.homeAdvantage,
            features.homeZGoalsSeason,
            features.awayZGoalsSeason,
            features.homeZWinsSeason,
            features.awayZWinsSeason
        ]


        print(baseline)
        
        return True 
        