import logging
from typing import Dict, Any, List
from pydantic import BaseModel

logger = logging.getLogger("ingres.evidence_scorer")

class EvidenceScore(BaseModel):
    item_title: str
    relevance: float
    authority: float
    freshness: float
    completeness: float
    composite_confidence: float

def score_retrieved_evidence(query: str, evidence_text: str, source_title: str) -> EvidenceScore:
    """
    Richer Evidence Scoring Layer (Missing Component 2):
    Scores each retrieved passage on Relevance, Authority, Freshness, Completeness,
    and calculates a Composite Confidence score.
    """
    clean_q = query.lower()
    clean_text = evidence_text.lower()

    # 1. Relevance Score: Keyword overlap ratio
    keywords = [w for w in clean_q.split() if len(w) > 3]
    matches = sum(1 for k in keywords if k in clean_text)
    relevance = round(min(1.0, max(0.1, matches / max(1, len(keywords)))), 2)

    # 2. Authority Score: Official report markers vs generic web text
    authority = 0.7
    if any(k in source_title.lower() for k in ["cgwb", "report", "official", "government", "tamil nadu"]):
        authority = 0.95

    # 3. Freshness Score: Date indicator matching
    freshness = 0.85
    if "2026" in evidence_text or "2025" in evidence_text:
        freshness = 0.98
    elif "2017" in evidence_text:
        freshness = 0.75

    # 4. Completeness Score: Specific numbers/names vs generic boilerplate
    has_numbers = any(c.isdigit() for c in evidence_text)
    has_specific_names = any(d in clean_text for d in ["salem", "coimbatore", "vellore", "chennai", "m bgl", "stage"])
    completeness = 0.5
    if has_numbers and has_specific_names:
        completeness = 0.9
    elif has_numbers:
        completeness = 0.7

    # 5. Composite Confidence (Weighted Average)
    composite = round((relevance * 0.4) + (authority * 0.25) + (freshness * 0.15) + (completeness * 0.20), 2)

    return EvidenceScore(
        item_title=source_title,
        relevance=relevance,
        authority=authority,
        freshness=freshness,
        completeness=completeness,
        composite_confidence=composite
    )
