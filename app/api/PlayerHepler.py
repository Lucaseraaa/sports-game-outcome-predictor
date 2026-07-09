import pandas as pd

class PlayerHelper:

    __player_dataset: pd.DataFrame 

    def __init__(
        self,
        dataframe_path: str
    ) -> None:
        
        # Importazione del dataset statico del costo dei giocatori 
        raw_dataset = pd.read_csv(dataframe_path)
        raw_dataset= raw_dataset.dropna() # Eliminazione delle righe contenenti un null

        # C
        raw_dataset["full_name"] = raw_dataset["first_name"] + " " + raw_dataset["last_name"]
        raw_dataset = raw_dataset.drop(columns=["first_name", "last_name"])

        # MultiIndex sulle colonne first_name e last_name
        self.__player_dataset = raw_dataset.set_index(["full_name"])
        self.__player_dataset = self.__player_dataset.sort_index()

    def get_player_market_value(self, full_name: str) -> float:
        """
        Metodo che permette di recuperare il valore di mercato di un giocatore (che simula una chiamata API)

        Args:
            full_name: nome e cognome del giocatore

        Return:
            costo del giocatore (se non viene trovato)  
        """

        try:
            
            # Ricerco il valore del giocatore
            return self.__player_dataset.loc[(full_name)].get("market_value").item()
        
        except KeyError:
            
            return 0.0 # Fallback: caso in cui il giocatore non esista nel dataframe
        
