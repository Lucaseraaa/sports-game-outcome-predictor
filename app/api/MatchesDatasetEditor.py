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
        if self.is_in_dataset(date, home_team, away_team):
            return False

        # Inserisco il record (con tutti i dati che servono)
        baseline = [date, home_team, away_team, statistics.homeGoal, statistics.awayGoal, statistics.fullTimeResult]

        # Calcolo della season
        sep_date = date.split('-')
        year, month = int(sep_date[0]), int(sep_date[1])
        last_year = year + 1 if month > 7 else year

        baseline.append(f"{last_year-1}-{last_year+1}")

        print(baseline)