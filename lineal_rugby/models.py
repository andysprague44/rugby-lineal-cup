from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, date


# DTOSs for the sportradar API
class Sport(BaseModel):
    id: str
    name: str


class Category(BaseModel):
    id: str
    name: str


class Competition(BaseModel):
    id: str
    name: str
    gender: str


class Season(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date
    year: str
    competition_id: str


class Competitor(BaseModel):
    id: str
    name: str
    country: Optional[str] = None
    gender: str


class SportEventContext(BaseModel):
    sport: Sport
    category: Category
    competition: Competition
    season: Season


class SportEvent(BaseModel):
    id: str
    start_time: datetime
    start_time_confirmed: bool
    sport_event_context: SportEventContext
    competitors: List[Competitor]


class SportEventStatus(BaseModel):
    status: str
    match_status: Optional[str] = None  # not present if cancelled
    # home_score: int
    # away_score: int
    winner_id: Optional[str] = None  # not present in case of a tie
    match_tie: bool = False  # not present unless a tie


class Summary(BaseModel):
    sport_event: SportEvent
    sport_event_status: SportEventStatus


class Competitions(BaseModel):
    generated_at: datetime
    competitions: List[Competition]


class Seasons(BaseModel):
    generated_at: datetime
    seasons: List[Season]


class SeasonSummary(BaseModel):
    generated_at: datetime
    summaries: List[Summary]
    season: Season = None
    competition: Competition = None


class SportRadarData(BaseModel):
    season_summaries: List[SeasonSummary] = []


# Domain models
class LinealCupEvent(BaseModel):
    start_time: datetime
    winner_name: str
    loser_name: str
    is_tie: bool
    gender: str
    competition_name: str


class LinearCupHolder(BaseModel):
    start_time: datetime
    holder: str


class LinearCupHolders(BaseModel):
    holders: List[LinearCupHolder] = []


class LinealCupStatistics(BaseModel):
    wins_by_country: Dict[str, int] = None


class LinealCup(BaseModel):
    competition_name: str
    gender: str
    events: List[LinealCupEvent]
    holders: LinearCupHolders = None
    current_holder: str = None
    statistics: LinealCupStatistics = None
