
from typing import List, Dict, Any
from pydantic import BaseModel

class SubmitRequest(BaseModel):
    language: str
    code: str

class SubmitResponse(BaseModel):
    result: str
    detail: List[Dict[str, Any]] | None = None
