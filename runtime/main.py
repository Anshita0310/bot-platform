"""Runtime API – serves dialog flows as interactive chatbot sessions."""

from __future__ import annotations

import logging
from typing import Any, Dict

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command

from .compiler import get_or_compile
from .config import ALLOWED_ORIGINS, RUNTIME_PORT
from .db import get_db
from .models import (
    InputPrompt,
    SendMessageRequest,
    SessionInfo,
    SessionResponse,
    StartSessionRequest,
)
from . import sessions

log = logging.getLogger("runtime")

app = FastAPI(title="Bot Builder Runtime")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────


def _extract_prompt(graph, config: dict) -> InputPrompt | None:
    """Read the interrupt payload from the graph snapshot."""
    try:
        snapshot = graph.get_state(config)
        if snapshot.next and snapshot.tasks:
            for task in snapshot.tasks:
                if task.interrupts:
                    raw = task.interrupts[0].value
                    return InputPrompt(**raw)
    except Exception:
        pass
    return None


def _graph_is_done(graph, config: dict) -> bool:
    """Return True when the graph has no more pending nodes."""
    try:
        snapshot = graph.get_state(config)
        return not snapshot.next
    except Exception:
        return True


def _build_response(
    session: sessions.Session,
    all_messages: list,
    graph,
) -> SessionResponse:
    """Build a SessionResponse with only the *new* messages."""
    new_msgs = all_messages[session.message_offset:]
    session.message_offset = len(all_messages)

    prompt = _extract_prompt(graph, session.config)
    if prompt:
        session.status = "waiting_input"
    elif _graph_is_done(graph, session.config):
        session.status = "completed"
    else:
        session.status = "active"

    return SessionResponse(
        session_id=session.id,
        messages=new_msgs,
        status=session.status,
        input_prompt=prompt,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────


@app.post("/api/sessions", status_code=201, response_model=SessionResponse)
async def start_session(req: StartSessionRequest, db=Depends(get_db)):
    """Create a session, compile the flow, and run until the first interrupt."""
    try:
        oid = ObjectId(req.flow_id)
    except Exception:
        raise HTTPException(400, "Invalid flow_id")

    flow_doc = await db.flows.find_one({"_id": oid})
    if not flow_doc:
        raise HTTPException(404, "Flow not found")

    graph = get_or_compile(flow_doc)
    session = sessions.create(req.flow_id)

    try:
        result = graph.invoke(
            {"messages": [], "variables": {}},
            session.config,
        )
    except Exception as exc:
        sessions.delete(session.id)
        log.exception("Graph invocation failed")
        raise HTTPException(500, f"Execution error: {exc}")

    all_messages = result.get("messages", [])
    return _build_response(session, all_messages, graph)


@app.post("/api/sessions/{session_id}/message", response_model=SessionResponse)
async def send_message(session_id: str, req: SendMessageRequest, db=Depends(get_db)):
    """Resume the graph with the user's text and advance to the next interrupt or END."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.status == "completed":
        raise HTTPException(400, "Session already completed")

    try:
        oid = ObjectId(session.flow_id)
    except Exception:
        raise HTTPException(400, "Invalid flow_id in session")

    flow_doc = await db.flows.find_one({"_id": oid})
    if not flow_doc:
        raise HTTPException(404, "Flow not found")

    graph = get_or_compile(flow_doc)

    try:
        result = graph.invoke(
            Command(resume=req.text),
            session.config,
        )
    except Exception as exc:
        log.exception("Graph resume failed")
        raise HTTPException(500, f"Execution error: {exc}")

    all_messages = result.get("messages", [])
    return _build_response(session, all_messages, graph)


@app.get("/api/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, db=Depends(get_db)):
    """Return metadata about an active session."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # Retrieve current variables from graph state
    variables: Dict[str, Any] = {}
    try:
        oid = ObjectId(session.flow_id)
        flow_doc = await db.flows.find_one({"_id": oid})
        if flow_doc:
            graph = get_or_compile(flow_doc)
            snapshot = graph.get_state(session.config)
            variables = snapshot.values.get("variables", {})
    except Exception:
        pass

    return SessionInfo(
        session_id=session.id,
        flow_id=session.flow_id,
        status=session.status,
        message_count=session.message_offset,
        variables=variables,
    )


@app.delete("/api/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """Delete a session."""
    if not sessions.delete(session_id):
        raise HTTPException(404, "Session not found")
    return Response(status_code=204)


@app.get("/health")
def health():
    return {"ok": True}
