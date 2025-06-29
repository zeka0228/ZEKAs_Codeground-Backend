import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.app.domain.match.service.match_service import MatchService  # ★ 매칭 루프
from src.app.domain.auth import router as auth_router
from src.app.domain.webrtc import router as webrtc_router
from src.app.domain.match import router as match_router
from src.app.domain.user import router as user_router
from src.app.domain.game import router as game_router
from src.app.config.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "resource" / "static"

match_service = MatchService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    match_service.start()  # 백그라운드 매칭 루프 시작
    yield
    await match_service.stop()  # 서버 종료 시 안전하게 취소


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specify allowed methods
    allow_headers=["Authorization", "Content-Type"],  # Specify allowed headers
)

app.include_router(router=auth_router, prefix=settings.API_V1_STR)
app.include_router(router=webrtc_router, prefix=settings.API_V1_STR)
app.include_router(router=match_router, prefix=settings.API_V1_STR)
app.include_router(router=user_router, prefix=settings.API_V1_STR)
app.include_router(router=game_router, prefix=settings.API_V1_STR)


@app.get("/")
async def health_check():
    return JSONResponse({"status": "ok"})


# test
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
