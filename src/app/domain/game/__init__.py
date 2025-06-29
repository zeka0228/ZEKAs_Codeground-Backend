from fastapi import APIRouter
from .router import submit_controller

router = APIRouter()
router.include_router(submit_controller.router, prefix="/game", tags=["game"])
