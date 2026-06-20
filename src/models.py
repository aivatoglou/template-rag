from pydantic import BaseModel
from typing import List

class APIRequest(BaseModel):
    message: str

class APIResponse(BaseModel):
    response: str
    sources: List[str] = []
    reasoning: str = ""
    model_id: str = ""
    duration_ms: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    tools_used: List[str] = []

class AgentResponse(BaseModel):
    answer: str
    sources: List[str]
