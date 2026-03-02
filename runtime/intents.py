"""Intent registry and classifier.

Uses sentence-transformers to encode user utterances and compares them
against a bank of example utterances per intent via cosine similarity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

log = logging.getLogger("runtime.intents")

# ---------------------------------------------------------------------------
# Mock intent definitions (Airtel customer-service demo)
# ---------------------------------------------------------------------------

@dataclass
class IntentDef:
    name: str
    description: str
    examples: List[str]
    flow_name: str            # must match seeded flow name in MongoDB


MOCK_INTENTS: List[IntentDef] = [
    IntentDef(
        name="recharge",
        description="Mobile recharge, prepaid plan, top-up balance",
        examples=[
            "I want to recharge my phone",
            "prepaid recharge",
            "top up my balance",
            "I need to recharge",
            "recharge my number",
            "add balance to my account",
        ],
        flow_name="Recharge Flow",
    ),
    IntentDef(
        name="billing",
        description="Bill payment, postpaid bill, billing issue",
        examples=[
            "I have a billing issue",
            "my bill is too high",
            "I want to pay my bill",
            "check my bill amount",
            "postpaid bill query",
            "when is my bill due",
        ],
        flow_name="Billing Flow",
    ),
    IntentDef(
        name="network_issue",
        description="Network problem, no signal, slow internet, connectivity",
        examples=[
            "my network is not working",
            "I have no signal",
            "internet is very slow",
            "call dropping issue",
            "no connectivity",
            "data is not working",
            "network problem",
        ],
        flow_name="Network Issue Flow",
    ),
    IntentDef(
        name="plan_change",
        description="Change plan, upgrade, downgrade, new plan",
        examples=[
            "I want to change my plan",
            "upgrade my plan",
            "show me available plans",
            "I want a better plan",
            "downgrade my plan",
            "what plans do you have",
        ],
        flow_name="Plan Change Flow",
    ),
    IntentDef(
        name="account",
        description="Account settings, profile, SIM related",
        examples=[
            "I want to update my account",
            "change my address",
            "I lost my SIM",
            "port my number",
            "update my profile",
            "SIM replacement",
        ],
        flow_name="Account Management Flow",
    ),
]

# ---------------------------------------------------------------------------
# Embedding cache (lazy-initialised)
# ---------------------------------------------------------------------------

_model = None
_intent_embeddings: Optional[np.ndarray] = None   # (N, dim)
_intent_labels: List[Tuple[str, str]] = []         # [(intent_name, flow_name), ...]


def _ensure_embeddings():
    """Build the embedding matrix on first call."""
    global _model, _intent_embeddings, _intent_labels

    if _intent_embeddings is not None:
        return

    from sentence_transformers import SentenceTransformer
    from .config import EMBEDDING_MODEL

    log.info("Loading embedding model '%s' …", EMBEDDING_MODEL)
    _model = SentenceTransformer(EMBEDDING_MODEL)

    all_texts: List[str] = []
    _intent_labels.clear()

    for intent in MOCK_INTENTS:
        for ex in intent.examples:
            all_texts.append(ex)
            _intent_labels.append((intent.name, intent.flow_name))

    _intent_embeddings = _model.encode(all_texts, normalize_embeddings=True)
    log.info("Indexed %d example utterances across %d intents.", len(all_texts), len(MOCK_INTENTS))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    intent: str
    flow_name: str
    score: float
    matched_example: str


def classify_intent(text: str, threshold: float = 0.45) -> Optional[ClassificationResult]:
    """Return the best-matching intent, or *None* if below *threshold*."""
    _ensure_embeddings()
    assert _model is not None and _intent_embeddings is not None

    query_emb = _model.encode([text], normalize_embeddings=True)

    # Cosine similarity (embeddings are already L2-normalised)
    sims = np.dot(query_emb, _intent_embeddings.T)[0]

    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])

    if best_score < threshold:
        return None

    intent_name, flow_name = _intent_labels[best_idx]

    # Recover the matching example text
    offset = 0
    matched = ""
    for intent in MOCK_INTENTS:
        if offset + len(intent.examples) > best_idx:
            matched = intent.examples[best_idx - offset]
            break
        offset += len(intent.examples)

    return ClassificationResult(
        intent=intent_name,
        flow_name=flow_name,
        score=round(best_score, 4),
        matched_example=matched,
    )


def list_intents() -> List[dict]:
    """Return a summary of all registered intents."""
    return [
        {"name": i.name, "description": i.description, "flow_name": i.flow_name}
        for i in MOCK_INTENTS
    ]
