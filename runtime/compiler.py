"""Compile a flow document (from MongoDB) into a runnable LangGraph."""

from __future__ import annotations

import re
from typing import Any, Dict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from .state import ConversationState
from .nlp import extract_entity, interpolate


# ── Graph cache (flow_id:version → compiled graph) ────────────────────────

_cache: Dict[str, Any] = {}


def get_or_compile(flow_doc: dict):
    """Return a cached compiled graph, or compile and cache a new one."""
    fid = str(flow_doc.get("_id", ""))
    ver = flow_doc.get("version", 1)
    key = f"{fid}:{ver}"
    if key not in _cache:
        _cache[key] = _compile(flow_doc)
    return _cache[key]


# ── Internal compilation ──────────────────────────────────────────────────

def _compile(flow_doc: dict):
    nodes_list = flow_doc.get("nodes", [])
    edges_list = flow_doc.get("edges", [])

    # Build lookup structures
    nodes_by_id: Dict[str, dict] = {}
    for n in nodes_list:
        data = n.get("data", {})
        ntype = data.get("type", n.get("type", "")).lower()
        nodes_by_id[n["id"]] = {**n, "_type": ntype, "_data": data}

    edges_by_source: Dict[str, list] = {}
    for e in edges_list:
        edges_by_source.setdefault(e["source"], []).append(e)

    # Identify start / end nodes
    start_id = None
    end_ids: set[str] = set()
    for nid, n in nodes_by_id.items():
        if n["_type"] == "start":
            start_id = nid
        elif n["_type"] == "end":
            end_ids.add(nid)

    if start_id is None:
        raise ValueError("Flow has no Start node")

    builder = StateGraph(ConversationState)

    # ── Add node functions ────────────────────────────────────────────────

    for nid, n in nodes_by_id.items():
        ntype = n["_type"]
        data = n["_data"]

        if ntype == "start":
            builder.add_node(nid, _make_passthrough())
        elif ntype == "end":
            builder.add_node(nid, _make_end(nid))
        elif ntype == "message":
            builder.add_node(nid, _make_message(nid, data))
        elif ntype == "entity":
            builder.add_node(nid, _make_entity(nid, data))
        elif ntype == "confirmation":
            builder.add_node(nid, _make_confirmation(nid, data))
        elif ntype == "tool":
            builder.add_node(nid, _make_tool(nid, data))
        else:
            # Unknown type → passthrough
            builder.add_node(nid, _make_passthrough())

    # ── Set entry point ───────────────────────────────────────────────────

    builder.set_entry_point(start_id)

    # ── Add edges ─────────────────────────────────────────────────────────

    for nid, n in nodes_by_id.items():
        ntype = n["_type"]
        out = edges_by_source.get(nid, [])

        if ntype == "end":
            builder.add_edge(nid, END)

        elif ntype == "confirmation":
            _add_confirmation_edges(builder, nid, out)

        else:
            if out:
                builder.add_edge(nid, out[0]["target"])

    # ── Compile with checkpointer ─────────────────────────────────────────

    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph


# ── Node factories ────────────────────────────────────────────────────────


def _make_passthrough():
    """Start or unknown node – no messages, just advance."""
    def fn(state: ConversationState):
        return {"messages": [], "variables": state.get("variables", {})}
    return fn


def _make_end(nid: str):
    def fn(state: ConversationState):
        return {
            "messages": [{"role": "system", "text": "Conversation ended.", "node_id": nid}],
        }
    return fn


def _make_message(nid: str, data: dict):
    raw_text = data.get("message", data.get("text", ""))

    def fn(state: ConversationState):
        text = interpolate(raw_text, state.get("variables", {}))
        return {
            "messages": [{"role": "bot", "text": text, "node_id": nid}],
        }
    return fn


def _make_entity(nid: str, data: dict):
    entity_name = data.get("entityName", "input")
    entity_type = data.get("entityType", "string")
    prompt_tpl = data.get("prompt", "") or f"Please provide your {entity_name}:"

    def fn(state: ConversationState):
        prompt = interpolate(prompt_tpl, state.get("variables", {}))

        # Pause execution; caller receives the prompt metadata.
        user_text = interrupt({
            "type": "entity",
            "prompt": prompt,
            "entity_name": entity_name,
            "entity_type": entity_type,
        })

        value = extract_entity(str(user_text), entity_type, entity_name)

        return {
            "messages": [
                {"role": "bot", "text": prompt, "node_id": nid},
                {"role": "user", "text": str(user_text)},
            ],
            "variables": {**state.get("variables", {}), entity_name: value},
        }
    return fn


def _make_confirmation(nid: str, data: dict):
    question_tpl = data.get("question", "Please confirm:")
    yes_label = data.get("yesLabel", "Yes")
    no_label = data.get("noLabel", "No")

    def fn(state: ConversationState):
        question = interpolate(question_tpl, state.get("variables", {}))

        user_text = interrupt({
            "type": "confirmation",
            "prompt": question,
            "yes_label": yes_label,
            "no_label": no_label,
        })

        is_yes = bool(
            re.match(r"^(yes|y|yeah|yep|sure|ok|confirm|1)$", str(user_text).strip(), re.IGNORECASE)
        )
        answer = "yes" if is_yes else "no"

        return {
            "messages": [
                {"role": "bot", "text": question, "node_id": nid},
                {"role": "user", "text": str(user_text)},
            ],
            "variables": {**state.get("variables", {}), "__last_confirmation__": answer},
        }
    return fn


def _make_tool(nid: str, data: dict):
    tool_name = data.get("toolName", "unknown")

    def fn(state: ConversationState):
        # Placeholder: a real deployment would call an external API here.
        return {
            "messages": [
                {"role": "bot", "text": f"⚙️ Running tool: {tool_name}", "node_id": nid},
                {"role": "bot", "text": f"✓ Tool \"{tool_name}\" executed successfully.", "node_id": nid},
            ],
        }
    return fn


# ── Confirmation routing ──────────────────────────────────────────────────

def _add_confirmation_edges(builder: StateGraph, nid: str, out_edges: list):
    """Add conditional edges that branch on __last_confirmation__."""
    yes_target = None
    no_target = None
    default_target = None

    for e in out_edges:
        handle = (e.get("sourceHandle") or e.get("data", {}).get("sourceHandle") or "").lower()
        if handle == "yes":
            yes_target = e["target"]
        elif handle == "no":
            no_target = e["target"]
        else:
            default_target = e["target"]

    # Fall back so every branch has *some* target
    yt = yes_target or default_target
    nt = no_target or default_target

    if yt is None and nt is None:
        # No outgoing edges at all → END
        builder.add_edge(nid, END)
        return

    def _router(state: ConversationState):
        answer = state.get("variables", {}).get("__last_confirmation__", "")
        if answer == "yes" and yt:
            return yt
        if answer == "no" and nt:
            return nt
        return yt or nt  # fallback

    # Tell LangGraph about all possible targets
    targets = {t for t in (yt, nt) if t}
    builder.add_conditional_edges(nid, _router, {t: t for t in targets})
