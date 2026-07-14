import pandas as pd
import difflib


class Odds:

    __odds_dataset: pd.DataFrame
    __match_dataset: pd.DataFrame
    __merged_dataset: pd.DataFrame

    def __merge_dataset(self) -> None:

        # Normalizzazione delle date
        self.__match_dataset['Match_Date_Temp'] = pd.to_datetime(
            self.__match_dataset['Date'], 
            errors='coerce' 
        ).dt.date

        self.__odds_dataset['Odds_Date_Temp'] = pd.to_datetime(
            self.__odds_dataset['matchDate'], 
            format="%d-%m-%y %H:%M", 
            errors='coerce' 
        ).dt.date

        # Risoluzione dei nomi delle squadre
        self.__match_dataset = self.__match_dataset.dropna(subset=['Match_Date_Temp'])
        self.__odds_dataset = self.__odds_dataset.dropna(subset=['Odds_Date_Temp'])
        match_teams = pd.concat([self.__match_dataset['HomeTeam'], self.__match_dataset['AwayTeam']]).unique()
        odds_teams = pd.concat([self.__odds_dataset['homeTeam'], self.__odds_dataset['awayTeam']]).unique()

        team_mapping = {}
        for team in odds_teams:
            matches = difflib.get_close_matches(team, match_teams, n=1, cutoff=0.5)
            team_mapping[team] = matches[0] if matches else team

        self.__odds_dataset['homeTeam_Norm'] = self.__odds_dataset['homeTeam'].map(team_mapping)
        self.__odds_dataset['awayTeam_Norm'] = self.__odds_dataset['awayTeam'].map(team_mapping)

        # Affiancamento dei due dataset
        self.__merged_dataset = pd.merge(
            left=self.__match_dataset,
            right=self.__odds_dataset,
            left_on=['Match_Date_Temp', 'HomeTeam', 'AwayTeam'],
            right_on=['Odds_Date_Temp', 'homeTeam_Norm', 'awayTeam_Norm'],
            how='inner' 
        )

        # Pulizia delle colonne temporanee create per il merge
        col_rimuovere_match = ['Match_Date_Temp']
        col_rimuovere_odds = ['Odds_Date_Temp', 'homeTeam_Norm', 'awayTeam_Norm']
        
        # Le puliamo sia dai dataset originali che dal dataset finale
        self.__match_dataset.drop(columns=col_rimuovere_match, inplace=True, errors='ignore')
        self.__odds_dataset.drop(columns=col_rimuovere_odds, inplace=True, errors='ignore')
        self.__merged_dataset.drop(columns=col_rimuovere_match + col_rimuovere_odds, inplace=True, errors='ignore')

    def __init__(
            self,
            odds_dataframe_path: str,
            match_dataframe_path
    ) -> None:

        # Importazione e rimozione delle rows vuote 
        self.__odds_dataset = pd.read_csv(odds_dataframe_path)
        self.__match_dataset = pd.read_csv(match_dataframe_path)
        self.__odds_dataset = self.__odds_dataset.dropna()

        # Merge dei due dataset
        self.__merge_dataset()
        print(self.__merged_dataset)

        
