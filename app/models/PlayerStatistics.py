from pydantic import BaseModel

class PlayerStatistics(BaseModel):

    homePlayers: list[str]
    awayPlayers: list[str]