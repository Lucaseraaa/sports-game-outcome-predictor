from pydantic import BaseModel

class PlayerStatistics(BaseModel):

    homePlayersValue: float
    awayPlayersValue: float