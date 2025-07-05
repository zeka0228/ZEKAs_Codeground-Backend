from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel
from src.app.models.models import MatchResult


@dataclass
class MatchingUserInfo:
    id: int
    mmr: float
    rd: float
    joined_at: datetime


class MatchLogSchema(BaseModel):
    match_log_id: int
    match_id: int
    problem_id: int
    result: Optional[MatchResult]
    mmr_earned: float
    opponent_mmr: float
    created_at: datetime

    class Config:
        from_attributes = True