from datetime import datetime
from dataclasses import dataclass


@dataclass
class MatchingUserInfo:
    id: int
    mmr: float
    rd: float
    joined_at: datetime
