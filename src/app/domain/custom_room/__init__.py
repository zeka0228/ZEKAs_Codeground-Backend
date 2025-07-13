from fastapi import APIRouter
from .router import custom_room_controller

router = APIRouter()
router.include_router(custom_room_controller.router, prefix="/custom_room", tags=["custom_room"])

