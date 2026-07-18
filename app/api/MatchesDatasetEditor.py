import pandas as pd
from app.models.Statistics import Statistics
from app.models.PredictionFeatures import PredictionFeatures


class MatchesDatasetEditor:

    __dataset: pd.DataFrame
    __dataset_path: str

    def __init__(
        self,
        dataset_path: str
    ) -> None:

        # Caricamento del dataset
        raw_dataset = pd.read_csv(dataset_path)

        self.__dataset = raw_dataset.set_index(["Date", "HomeTeam", "AwayTeam"])
        self.__dataset = self.__dataset.sort_index()
        self.__dataset_path = dataset_path
    
    def get_all_match_of_day(self, season: str, day: int) -> list:
        """
        Metodo che ritorna le partite della giornata selezionata
        
        Args:
            season: stagione
            day: giornata della partita
        
        Returns:
            lista delle partite
        """

        # Maschera per la ricerca
        mask = (self.__dataset['Season'] == season) & (self.__dataset['Day'] == day)
        
        # Applicazione del filtro
        matches_df = self.__dataset[mask]

        return matches_df.reset_index().to_dict(orient='records')


    def add_new_matches(self, new_matches_list: list) -> None:
        """
        Inserisce le nuove partite nel dataset, aggiorna il dataframe in memoria
        e sovrascrive il file CSV originale.
        """
        if not new_matches_list:
            return  

        new_df = pd.DataFrame(new_matches_list)
        new_df = new_df.set_index(["Date", "HomeTeam", "AwayTeam"])
        self.__dataset = pd.concat([self.__dataset, new_df])
        self.__dataset = self.__dataset[~self.__dataset.index.duplicated(keep='last')]
        self.__dataset = self.__dataset.sort_index()

        self.__dataset.to_csv(self.__dataset_path)

    def extract_from_dataset(self, date: str, home_team: str, away_team: str):
        """
        Metodo che permette di estrarre un record dal dataframe (se esiste)
        """

        if not self.is_in_dataset(date, home_team, away_team):
            return None
        
        try:
            return self.__dataset.loc[(date, home_team, away_team)]
        except KeyError:
            # Nel caso in cui per qualche motivo la riga non venisse trovata
            return None

    def update_match_results(self, updates_list: list) -> None:
        """
        Aggiorna i risultati finali (FTHG, FTAG, FTR) per le partite già presenti.
        
        Args:
            updates_list: Lista di dizionari con i risultati aggiornati.
        """
        if not updates_list:
            return

        for update in updates_list:
            # Creiamo la tupla indice per trovare la riga esatta
            idx = (update["Date"], update["HomeTeam"], update["AwayTeam"])
            
            # Se la partita esiste nel dataset, aggiorniamo i valori
            if idx in self.__dataset.index:
                self.__dataset.at[idx, 'FTHG'] = update['FTHG']
                self.__dataset.at[idx, 'FTAG'] = update['FTAG']
                self.__dataset.at[idx, 'FTR'] = update['FTR']
                
                # Se hai anche queste colonne nel CSV, puoi scommentare:
                self.__dataset.at[idx, 'HST'] = update.get('HST')
                self.__dataset.at[idx, 'AST'] = update.get('AST')

        # Salviamo le modifiche nel CSV
        self.__dataset.to_csv(self.__dataset_path)

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

    def __expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calcola la probabilità di vittoria attesa (Expected Score)."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def __goal_multiplier(self, goal_diff: int) -> float:
        """Calcola il moltiplicatore in base alla differenza reti."""
        margin = abs(goal_diff)
        if margin <= 1:
            return 1.0
        elif margin == 2:
            return 1.5
        else:
            return (11.0 + margin) / 8.0

    def __get_elo(self, team: str, match_date: str, day: int) -> float:
        """
        Calcola l'Elo rating della squadra simulando i risultati storici fino 
        alla data della partita attuale.
        
        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            Valore Elo (float). Ritorna il valore di default (1500.0) in caso di assenza di dati storici.
        """
        # Parametri dell'ELO
        initial_elo = 1500.0
        home_advantage = 100.0
        k_factor = 20.0
        
        df = self.__dataset.reset_index()

        # Per l'ELO prendiamo TUTTO lo storico precedente alla data del match, non solo la stagione corrente.
        # È fondamentale ordinarli per data per calcolare correttamente l'evoluzione dell'Elo.
        past_matches = df[df["Date"] < match_date].sort_values(by='Date')

        if past_matches.empty:
            return initial_elo

        current_elo = {}

        # Ricalcola l'Elo iterativamente per le partite passate
        for _, row in past_matches.iterrows():
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            
            hg = row['FTHG']
            ag = row['FTAG']

            # Gestione valori nulli: salta la partita se non c'è un risultato valido
            if pd.isna(hg) or pd.isna(ag):
                continue

            # Inizializzazione delle nuove squadre
            if home_team not in current_elo: current_elo[home_team] = initial_elo
            if away_team not in current_elo: current_elo[away_team] = initial_elo

            elo_h_pre = current_elo[home_team]
            elo_a_pre = current_elo[away_team]

            e_home = self.__expected_score(elo_h_pre + home_advantage, elo_a_pre)
            e_away = self.__expected_score(elo_a_pre, elo_h_pre + home_advantage)

            # Assegnazione punti vittoria/pareggio/sconfitta
            if hg > ag:
                s_home, s_away = 1.0, 0.0
            elif hg < ag:
                s_home, s_away = 0.0, 1.0
            else:
                s_home, s_away = 0.5, 0.5

            g = self.__goal_multiplier(hg - ag)
            
            # Aggiornamento
            current_elo[home_team] = elo_h_pre + k_factor * g * (s_home - e_home)
            current_elo[away_team] = elo_a_pre + k_factor * g * (s_away - e_away)

        # Ritorna l'Elo calcolato per la squadra richiesta, o 1500.0 se la squadra è debuttante
        return current_elo.get(team, initial_elo)

    def __get_points(self, team: str, match_date: str, day: int) -> int:
        """
        Metodo utilizzato per calcolare i punti in classifica della squadra 
        nel campionato in corso, prima della disputa della partita indicata.
        Regola: +3 punti per vittoria, +1 punto per pareggio, 0 punti per sconfitta.

        Args:
            team: team di riferimento
            match_date: data della partita in formato YYYY-MM-DD
            day: giornata corrente di campionato

        Returns:
            Punti totali in classifica (int) accumulati prima della partita.
            Ritorna 0 in caso di prima giornata o se non ci sono partite precedenti.
        """
        # Caso limite: prima giornata
        if day == 1:
            return 0

        # Inizio della stagione
        year = int(match_date[:4])
        month = int(match_date[5:7])

        season_start_year = year if month > 7 else year - 1
        season_start = f"{season_start_year}-08-01"

        df = self.__dataset.reset_index()

        is_playing = (df["HomeTeam"] == team) | (df["AwayTeam"] == team)
        is_current_season_past = (df["Date"] >= season_start) & (df["Date"] < match_date)

        past_matches = df[is_playing & is_current_season_past]

        if past_matches.empty:
            return 0

        points = 0

        for _, match in past_matches.iterrows():
            if match["HomeTeam"] == team:
                if match["FTR"] == "H":
                    points += 3
                elif match["FTR"] == "D":
                    points += 1
            else:
                if match["FTR"] == "A":
                    points += 3
                elif match["FTR"] == "D":
                    points += 1

        return points

    def generate_prediction_features(self, day: int, home_team: str, away_team: str, match_date: str) -> PredictionFeatures:
        """
        Metodo utilizzato per generare le feature necessarie per la predizione 
        Args:
            day: giornata di campionato
            statistics: statistiche della partita
        
        Returns:
            istanza della classe che indica i valori necessari alle previsioni
        """

        return PredictionFeatures(
            homeWinStreak=self.__get_winstreak(home_team, match_date, day),
            awayWinStreak=self.__get_winstreak(away_team, match_date, day),
            homeGoalOnShotRatio=self.__get_goal_on_shot_ratio(home_team, match_date, day),
            awayGoalOnShotRatio=self.__get_goal_on_shot_ratio(away_team, match_date, day),
            homePointToMatchRatio=self.__get_point_to_match_ratio(home_team, match_date, day),
            awayPointToMatchRatio=self.__get_point_to_match_ratio(away_team, match_date, day),
            homeAdvantage=self.__get_home_advantage(home_team, match_date, day),
            homeZGoalsSeason=self.__get_z_goals(home_team, match_date, day),
            awayZGoalsSeason=self.__get_z_goals(away_team, match_date, day),
            homeZWinsSeason=self.__get_z_wins(home_team, match_date, day),
            awayZWinsSeason=self.__get_z_wins(away_team, match_date, day),
            eloHome=self.__get_elo(home_team, match_date, day),
            eloAway=self.__get_elo(away_team, match_date, day),
            pointsHome=self.__get_points(home_team, match_date, day),            
            pointsAway=self.__get_points(away_team, match_date, day),            
        )

    def add_match_in_dataset(self, day: int, home_team: str, away_team: str, match_date: str):
        """
        Metodo che permette di inserire un record di dati (a partita non ancora conclusa) nel dataset
        """

        if self.is_in_dataset(match_date, home_team, away_team):
            return False
        
        baseline = [match_date, home_team, away_team, 0, 0, '']

        sep_date = match_date.split('-')
        year, month = int(sep_date[0]), int(sep_date[1])
        start_year = year if month > 7 else year - 1
        baseline.append(f"{start_year}-{start_year+1}")

        features = self.generate_prediction_features(day, home_team, away_team, match_date)

        baseline += [
            features.homeWinStreak,
            features.awayWinStreak,
            features.homeZGoalsSeason,
            features.awayZGoalsSeason,
            features.homeZWinsSeason,
            features.awayZWinsSeason,
            features.homeGoalOnShotRatio,
            features.awayGoalOnShotRatio,
            features.homeAdvantage,
            features.eloHome,
            features.eloAway,
            features.pointsHome,
            features.pointsAway,
            0,
            0,
            features.homePointToMatchRatio,
            features.awayPointToMatchRatio,
        ]

        # Separo la chiave dell'indice (date, home_team, away_team) dai valori delle colonne
        index_key = tuple(baseline[:3])
        row_values = baseline[3:]

        # Creo un DataFrame di una sola riga con lo stesso indice/colonne del dataset
        new_row = pd.DataFrame(
            [row_values],
            columns=self.__dataset.columns,
            index=pd.MultiIndex.from_tuples([index_key], names=self.__dataset.index.names)
        )

        # Concateno e riordino
        self.__dataset = pd.concat([self.__dataset, new_row])
        self.__dataset = self.__dataset.sort_index()

        try:
            self.__dataset.to_csv(self.__dataset_path)
        except Exception as e:
            print(f"Eccezione: {e}")
            return False

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
        print(f"Data della partita: {date}")

        if self.is_in_dataset(date, home_team, away_team):
            return False

        baseline = [date, home_team, away_team, statistics.homeGoal, statistics.awayGoal, statistics.fullTimeResult]

        sep_date = date.split('-')
        year, month = int(sep_date[0]), int(sep_date[1])
        start_year = year if month > 7 else year - 1
        baseline.append(f"{start_year}-{start_year+1}")

        features = self.generate_prediction_features(day, statistics)

        baseline += [
            features.homeWinStreak,
            features.awayWinStreak,
            features.homeZGoalsSeason,
            features.awayZGoalsSeason,
            features.homeZWinsSeason,
            features.awayZWinsSeason,
            features.homeGoalOnShotRatio,
            features.awayGoalOnShotRatio,
            features.homeAdvantage,
            features.eloHome,
            features.eloAway,
            features.pointsHome,
            features.pointsAway,
            0,
            0,
            features.homePointToMatchRatio,
            features.awayPointToMatchRatio,
        ]

        # Separo la chiave dell'indice (date, home_team, away_team) dai valori delle colonne
        index_key = tuple(baseline[:3])
        row_values = baseline[3:]

        # Creo un DataFrame di una sola riga con lo stesso indice/colonne del dataset
        new_row = pd.DataFrame(
            [row_values],
            columns=self.__dataset.columns,
            index=pd.MultiIndex.from_tuples([index_key], names=self.__dataset.index.names)
        )

        # Concateno e riordino
        self.__dataset = pd.concat([self.__dataset, new_row])
        self.__dataset = self.__dataset.sort_index()

        try:
            self.__dataset.to_csv(self.__dataset_path)
        except Exception as e:
            print(f"Eccezione: {e}")
            return False

        return True
        