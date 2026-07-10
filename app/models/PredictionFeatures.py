from pydantic import BaseModel


class PredictionFeatures(BaseModel):
    
    # WinStreak
    homeWinStreak: int
    awayWinStreak: int

    # GoalOnShotRatio
    homeGoalOnShotRatio: float
    awayGoalOnShotRatio: float

    # PointToMatchRatio
    homePointToMatchRatio: float
    awayPointToMatchRatio: float

    # HomeAdvantage
    homeAdvantage: float

    # Z-Scores
    homeZGoalsSeason: float
    awayZGoalsSeason: float
    homeZWinsSeason: float
    awayZWinsSeason: float
    
    