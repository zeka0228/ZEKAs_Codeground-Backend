from src.app.models.models import Problem
from sqlalchemy import func
from sqlalchemy.orm import Session

TIER_PRIORITY = ["bronze", "silver", "gold", "platinum", "diamond", "challenger"]

def get_higher_tier(tier1: str, tier2: str):
    return max([tier1, tier2], key=lambda t: TIER_PRIORITY.index(t))

def select_problem_for_tiers(db: Session, tier1: str, tier2: str):
    selected_tier = get_higher_tier(tier1, tier2)
    return (
        db.query(Problem)
        .filter(Problem.difficulty == selected_tier)
        .order_by(func.random())
        .first()
    )