from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.app.models.models import Problem
import random


async def get_random_problem(db: Session) -> Problem:
    max_id = db.scalar(select(func.max(Problem.problem_id)))
    if max_id is None:
        raise Exception("No problems exist")

    while True:
        random_id = random.randint(1, max_id)
        problem = db.scalar(select(Problem).where(Problem.problem_id == random_id))
        if problem:
            return problem
