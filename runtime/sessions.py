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


# ── Call sessions (voice-bot) ─────────────────────────────────────────────


@dataclass
class CallSession:
    id: str
    phase: str = "awaiting_intent"   # awaiting_intent | flow_active | completed
    intent: Optional[str] = None
    flow_id: Optional[str] = None
    graph_config: Optional[Dict[str, Any]] = None
    message_offset: int = 0
    messages: list = field(default_factory=list)  # welcome + intent-phase msgs


_call_store: Dict[str, CallSession] = {}


def create_call() -> CallSession:
    cid = uuid.uuid4().hex
    call = CallSession(id=cid)
    _call_store[cid] = call
    return call


def get_call(call_id: str) -> Optional[CallSession]:
    return _call_store.get(call_id)


def delete_call(call_id: str) -> bool:
    return _call_store.pop(call_id, None) is not None
