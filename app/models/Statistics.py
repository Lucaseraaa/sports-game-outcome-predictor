from pydantic import BaseModel

from app.models.Team import Team

class Statistics(BaseModel):
    
    # Squadre
    homeTeam: Team
    awayTeam: Team

    # Goal
    homeGoal: int
    awayGoal: int 
    fullTimeResult: str

    # Shots
    homeShots: int
    awayShots: int

    # Date
    matchDate: str