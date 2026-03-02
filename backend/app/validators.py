from typing import Set, Dict, List
from .schemas import FlowBase

# Accepted node types (frontend vocabulary)
VALID_NODE_TYPES = {"start", "end", "message", "entity", "confirmation", "tool"}


def validate_flow(flow: FlowBase):
    id_to_node = {n.id: n for n in flow.nodes}

    # 0) All node types are known
    for n in flow.nodes:
        if n.type.lower() not in VALID_NODE_TYPES:
            raise ValueError(f"Unknown node type '{n.type}' on node {n.id}")

    # 1) Nodes exist for all edges
    for e in flow.edges:
        if e.source not in id_to_node:
            raise ValueError(f"Edge {e.id} references missing source node {e.source}")
        if e.target not in id_to_node:
            raise ValueError(f"Edge {e.id} references missing target node {e.target}")

    # 2) Exactly one Start, >=1 End
    starts = [n for n in flow.nodes if n.type.lower() == "start"]
    ends = [n for n in flow.nodes if n.type.lower() == "end"]
    if len(starts) != 1:
        raise ValueError(f"Flow must have exactly 1 Start node (found {len(starts)})")
    if len(ends) < 1:
        raise ValueError("Flow must have at least 1 End node")

    # 3) No cycles (simple DFS)
    adj: Dict[str, List[str]] = {}
    for e in flow.edges:
        adj.setdefault(e.source, []).append(e.target)

    visited: Set[str] = set()
    stack: Set[str] = set()

    def dfs(u: str):
        visited.add(u)
        stack.add(u)
        for v in adj.get(u, []):
            if v not in visited:
                dfs(v)
            elif v in stack:
                raise ValueError(f"Cycle detected at node {v}")
        stack.remove(u)

    dfs(starts[0].id)

    # 4) Reachability: all End nodes reachable from Start
    reachable = set()
    def mark(u: str):
        reachable.add(u)
        for v in adj.get(u, []):
            if v not in reachable:
                mark(v)
    mark(starts[0].id)

    for end in ends:
        if end.id not in reachable:
            raise ValueError(f"End node {end.id} is not reachable from Start")

    return True
