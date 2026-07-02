from pydantic import BaseModel
from app.models.Team import Team


class Match(BaseModel):
    id: int
    date: str
    homeTeam: Team
    awayTeam: Team

class Matches(BaseModel):
    data: list[Match]

