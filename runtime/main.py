"""Runtime API – serves dialog flows as interactive chatbot sessions."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command

from .compiler import get_or_compile
from .config import ALLOWED_ORIGINS, RUNTIME_PORT
from .db import get_db
from .intents import classify_intent, list_intents
from .models import (
    CallInfo,
    CallResponse,
    DetectedIntent,
    InputPrompt,
    SendMessageRequest,
    SessionInfo,
    SessionResponse,
    StartSessionRequest,
)
from .seed import seed_mock_flows, ORG_ID, PROJECT_ID
from . import sessions

log = logging.getLogger("runtime")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed mock flows on startup."""
    db = await get_db()
    await seed_mock_flows(db)
    yield


app = FastAPI(title="Bot Builder Runtime", lifespan=lifespan)

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


# ── Voice-bot call endpoints ──────────────────────────────────────────────

WELCOME_MESSAGE = "Hi, welcome to Airtel. How can I help you today?"


@app.post("/api/calls", status_code=201, response_model=CallResponse)
async def start_call():
    """Initiate a voice-bot call. Returns the welcome greeting."""
    call = sessions.create_call()
    welcome = {"role": "bot", "text": WELCOME_MESSAGE}
    call.messages.append(welcome)
    return CallResponse(
        call_id=call.id,
        messages=[welcome],
        status="awaiting_intent",
    )


@app.post("/api/calls/{call_id}/message", response_model=CallResponse)
async def call_message(call_id: str, req: SendMessageRequest, db=Depends(get_db)):
    """Handle a user utterance during a call.

    Phase 1 (awaiting_intent):
        Classify intent → find flow → compile → start executing.
    Phase 2 (flow_active):
        Resume the LangGraph execution with user input.
    """
    call = sessions.get_call(call_id)
    if not call:
        raise HTTPException(404, "Call not found")
    if call.phase == "completed":
        raise HTTPException(400, "Call already completed")

    call.messages.append({"role": "user", "text": req.text})

    # ── Phase 1: intent detection ─────────────────────────────────────
    if call.phase == "awaiting_intent":
        result = classify_intent(req.text)

        if result is None:
            # No intent matched — ask again
            retry_msg = {"role": "bot", "text": "I'm sorry, I didn't quite catch that. Could you tell me what you need help with? For example: recharge, billing, network issue, plan change, or account query."}
            call.messages.append(retry_msg)
            return CallResponse(
                call_id=call.id,
                messages=[retry_msg],
                status="awaiting_intent",
            )

        # Intent matched — find the corresponding flow in MongoDB
        detected = DetectedIntent(
            intent=result.intent,
            flow_name=result.flow_name,
            score=result.score,
            matched_example=result.matched_example,
        )

        flow_doc = await db.flows.find_one({
            "orgId": ORG_ID,
            "projectId": PROJECT_ID,
            "name": result.flow_name,
        })
        if not flow_doc:
            raise HTTPException(500, f"Seeded flow '{result.flow_name}' not found in DB")

        # Compile and start executing the flow
        graph = get_or_compile(flow_doc)
        call.intent = result.intent
        call.flow_id = str(flow_doc["_id"])
        call.graph_config = {"configurable": {"thread_id": call.id}}

        try:
            state = graph.invoke(
                {"messages": [], "variables": {}},
                call.graph_config,
            )
        except Exception as exc:
            log.exception("Graph invocation failed")
            raise HTTPException(500, f"Execution error: {exc}")

        # Collect new messages from the flow
        flow_msgs = state.get("messages", [])
        for m in flow_msgs:
            call.messages.append(m)

        prompt = _extract_prompt(graph, call.graph_config)
        if prompt:
            call.phase = "flow_active"
        elif _graph_is_done(graph, call.graph_config):
            call.phase = "completed"
        else:
            call.phase = "flow_active"

        return CallResponse(
            call_id=call.id,
            messages=flow_msgs,
            status=call.phase,
            detected_intent=detected,
            input_prompt=prompt,
        )

    # ── Phase 2: flow execution ───────────────────────────────────────
    if not call.flow_id or not call.graph_config:
        raise HTTPException(400, "Call has no active flow")

    flow_doc = await db.flows.find_one({"_id": ObjectId(call.flow_id)})
    if not flow_doc:
        raise HTTPException(404, "Flow not found")

    graph = get_or_compile(flow_doc)

    try:
        state = graph.invoke(Command(resume=req.text), call.graph_config)
    except Exception as exc:
        log.exception("Graph resume failed")
        raise HTTPException(500, f"Execution error: {exc}")

    all_msgs = state.get("messages", [])
    new_msgs = all_msgs[call.message_offset:]
    call.message_offset = len(all_msgs)
    for m in new_msgs:
        call.messages.append(m)

    prompt = _extract_prompt(graph, call.graph_config)
    if prompt:
        call.phase = "flow_active"
    elif _graph_is_done(graph, call.graph_config):
        call.phase = "completed"

    return CallResponse(
        call_id=call.id,
        messages=new_msgs,
        status=call.phase,
        input_prompt=prompt,
    )


@app.get("/api/calls/{call_id}", response_model=CallInfo)
async def get_call_info(call_id: str, db=Depends(get_db)):
    """Return metadata about an active call."""
    call = sessions.get_call(call_id)
    if not call:
        raise HTTPException(404, "Call not found")

    variables: Dict[str, Any] = {}
    if call.flow_id and call.graph_config:
        try:
            flow_doc = await db.flows.find_one({"_id": ObjectId(call.flow_id)})
            if flow_doc:
                graph = get_or_compile(flow_doc)
                snapshot = graph.get_state(call.graph_config)
                variables = snapshot.values.get("variables", {})
        except Exception:
            pass

    return CallInfo(
        call_id=call.id,
        phase=call.phase,
        intent=call.intent,
        flow_id=call.flow_id,
        message_count=len(call.messages),
        variables=variables,
    )


@app.delete("/api/calls/{call_id}", status_code=204)
async def end_call(call_id: str):
    if not sessions.delete_call(call_id):
        raise HTTPException(404, "Call not found")
    return Response(status_code=204)


@app.get("/api/intents")
def get_intents():
    """List all registered intents."""
    return list_intents()


@app.get("/health")
def health():
    return {"ok": True}
