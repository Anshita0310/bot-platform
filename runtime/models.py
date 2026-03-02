from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class StartSessionRequest(BaseModel):
    flow_id: str


class SendMessageRequest(BaseModel):
    text: str


class InputPrompt(BaseModel):
    """Describes what user input the bot is waiting for."""
    type: str  # "entity" or "confirmation"
    prompt: str
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None
    yes_label: Optional[str] = None
    no_label: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    status: str  # "waiting_input" | "completed"
    input_prompt: Optional[InputPrompt] = None


class SessionInfo(BaseModel):
    session_id: str
    flow_id: str
    status: str
    message_count: int
    variables: Dict[str, Any]
