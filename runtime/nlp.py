"""NLP utilities: entity extraction and variable interpolation."""

import re
from typing import List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Variable interpolation
# ---------------------------------------------------------------------------

def interpolate(text: str, variables: dict) -> str:
    """Replace ``{{varName}}`` placeholders with values from *variables*."""
    def _replacer(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(variables.get(key, m.group(0)))
    return re.sub(r"\{\{(\w+)\}\}", _replacer, text)


# ---------------------------------------------------------------------------
# Regex-based entity extraction
# ---------------------------------------------------------------------------

_EXTRACTORS = {
    "number": re.compile(r"-?\d+(?:\.\d+)?"),
    "email": re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+"),
    "phone": re.compile(r"[\d\-+() ]{7,}"),
    "date": re.compile(
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"       # 2024-03-15
        r"|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"     # 03/15/2024
        r"|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}(?:,?\s*\d{4})?",
        re.IGNORECASE,
    ),
    "boolean": re.compile(
        r"^(yes|y|yeah|yep|sure|ok|1|true|no|n|nope|nah|0|false)$", re.IGNORECASE
    ),
}


def extract_entity(text: str, entity_type: str, entity_name: str = "") -> str:
    """Pull a typed value out of free-form user text.

    Falls back to the raw text if no pattern matches.
    """
    text = text.strip()
    if not text:
        return text

    pattern = _EXTRACTORS.get(entity_type)
    if pattern is None:
        return text  # "string", "custom", or unknown → pass through

    m = pattern.search(text)
    if m is None:
        return text

    value = m.group().strip()

    # Normalise booleans
    if entity_type == "boolean":
        return (
            "true"
            if re.match(r"^(yes|y|yeah|yep|sure|ok|1|true)$", value, re.IGNORECASE)
            else "false"
        )
    return value


# ---------------------------------------------------------------------------
# Semantic matching (sentence-transformers) — lazy-loaded
# ---------------------------------------------------------------------------

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from .config import EMBEDDING_MODEL

        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def semantic_match(text: str, candidates: List[str], threshold: float = 0.5) -> Optional[str]:
    """Return the closest candidate by cosine similarity, or *None* if below *threshold*."""
    if not candidates:
        return None
    model = _get_model()
    text_emb = model.encode([text])
    cand_embs = model.encode(candidates)
    sims = np.dot(text_emb, cand_embs.T)[0]
    best_idx = int(np.argmax(sims))
    if sims[best_idx] >= threshold:
        return candidates[best_idx]
    return None
