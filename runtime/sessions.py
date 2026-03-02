"""In-memory session store.

Each session maps to one LangGraph thread and tracks how many messages
have already been returned to the client (``message_offset``).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Session:
    id: str
    flow_id: str
    config: Dict[str, Any]   # {"configurable": {"thread_id": ...}}
    message_offset: int = 0  # messages already sent to the client
    status: str = "active"   # active | waiting_input | completed


_store: Dict[str, Session] = {}


def create(flow_id: str) -> Session:
    sid = uuid.uuid4().hex
    session = Session(
        id=sid,
        flow_id=flow_id,
        config={"configurable": {"thread_id": sid}},
    )
    _store[sid] = session
    return session


def get(session_id: str) -> Optional[Session]:
    return _store.get(session_id)


def delete(session_id: str) -> bool:
    return _store.pop(session_id, None) is not None


def list_all() -> list[Session]:
    return list(_store.values())
