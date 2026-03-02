from typing import Dict, Any
from .schemas import FlowBase


def _contains(text: str, sub: str) -> bool:
    return sub.lower() in str(text).lower()


def _equals(a: Any, b: Any) -> bool:
    return str(a).strip().lower() == str(b).strip().lower()


def eval_condition(expr: str, ctx: Dict[str, Any]) -> bool:
    # Minimal DSL: contains(var, 'text'), equals(var, 'value'), else
    if not isinstance(expr, str):
        return False
    s = expr.strip()
    if s == "else":
        return True
    if s.startswith("contains(") and s.endswith(")"):
        inner = s[len("contains("):-1]
        if "," not in inner:
            return False
        var, val = inner.split(",", 1)
        var = var.strip()
        val = val.strip().strip("'").strip('"')
        return _contains(ctx.get(var, ""), val)
    if s.startswith("equals(") and s.endswith(")"):
        inner = s[len("equals("):-1]
        if "," not in inner:
            return False
        var, val = inner.split(",", 1)
        var = var.strip()
        val = val.strip().strip("'").strip('"')
        return _equals(ctx.get(var), val)
    return False


def run_once(flow: FlowBase, user_inputs: Dict[str, Any]) -> Dict[str, Any]:
    nodes = {n.id: n for n in flow.nodes}
    edges = {}
    for e in flow.edges:
        edges.setdefault(e.source, []).append(e)

    ctx: Dict[str, Any] = {**(user_inputs or {})}
    transcript = []

    start_id = next(n.id for n in flow.nodes if n.type.lower() == "start")
    current = start_id
    visited_steps = 0
    safety_limit = 1000

    while visited_steps < safety_limit and current is not None:
        visited_steps += 1
        node = nodes[current]
        ntype = node.type.lower()

        if ntype == "message":
            transcript.append({"role": "bot", "text": node.data.get("message", node.data.get("text", ""))})
            next_edges = edges.get(current, [])
            current = next_edges[0].target if next_edges else None

        elif ntype == "entity":
            var = node.data.get("entityName", node.data.get("variable", "user_input"))
            transcript.append({"role": "bot", "text": node.data.get("prompt", f"Please provide {var}")})
            transcript.append({"role": "user", "var": var, "value": ctx.get(var, "")})
            next_edges = edges.get(current, [])
            current = next_edges[0].target if next_edges else None

        elif ntype == "confirmation":
            conds = node.data.get("conditions", [])
            target = None
            for c in conds:
                if eval_condition(c.get("when", "else"), ctx):
                    target = c.get("to")
                    break
            if not target:
                next_edges = edges.get(current, [])
                target = next_edges[0].target if next_edges else None
            current = target

        elif ntype == "tool":
            transcript.append({"role": "bot", "text": f"[tool: {node.data.get('toolName', 'unknown')}]"})
            next_edges = edges.get(current, [])
            current = next_edges[0].target if next_edges else None

        elif ntype == "start":
            next_edges = edges.get(current, [])
            current = next_edges[0].target if next_edges else None

        elif ntype == "end":
            break

        else:
            next_edges = edges.get(current, [])
            current = next_edges[0].target if next_edges else None

    return {"transcript": transcript, "context": ctx}
