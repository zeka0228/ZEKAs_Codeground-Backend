import httpx
from fastapi import HTTPException
from src.app.config.config import settings

async def evaluate_code(language: str, code: str):
    payload = {
        "language": language,
        "code": code,
        "stdins": [],
        "timeLimit": 30000,
        "memoryLimit": 256,
        "token": None,
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(settings.ONLINE_JUDGE_HOST_ENDPOINT, json=payload)
            response.raise_for_status()
            results = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Judge request failed")
        except httpx.HTTPError:
            raise HTTPException(status_code=500, detail="Judge service unreachable")
    success = all(res.get("exitCode") == 0 for res in results)
    return {"result": "correct" if success else "wrong", "detail": results}
