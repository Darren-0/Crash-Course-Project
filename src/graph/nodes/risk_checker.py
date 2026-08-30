import re
from typing import Any, Dict, List

from src.graph.state import FinancialAnalysisState


RISK_TERMS = {
    "liquidity": r"\bliquidity\b|working capital|cash flow",
    "leverage": r"\bdebt\b|indebtedness|covenant|leverage",
    "legal": r"litigation|legal proceedings|regulatory",
    "market": r"competition|demand|recession|market conditions",
}

# Rough chars-per-token heuristic (~4 chars/token for English text).
# Not exact for every local model's tokenizer, but good enough for a
# conservative safety margin. If your ollama setup exposes a tokenize
# endpoint, swap this out for a real count.
CHARS_PER_TOKEN = 4
MAX_DIGEST_TOKENS = 1500  # leave plenty of room for prompt + other sections
SNIPPET_WINDOW = 250      # chars of context around each match
MAX_SNIPPETS_PER_CATEGORY = 4


def _char_budget() -> int:
    return MAX_DIGEST_TOKENS * CHARS_PER_TOKEN


def _get_snippets(text: str, pattern: str, window: int, max_snippets: int) -> List[str]:
    """Pull windows of text around each regex match, merging overlaps."""
    spans = []
    for m in re.finditer(pattern, text, flags=re.IGNORECASE):
        start = max(0, m.start() - window)
        end = min(len(text), m.end() + window)
        spans.append((start, end))
        if len(spans) >= max_snippets:
            break

    if not spans:
        return []

    # Merge overlapping/adjacent spans so we don't duplicate text
    spans.sort()
    merged = [spans[0]]
    for start, end in spans[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 50:  # close enough to merge
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return [text[s:e].strip() for s, e in merged]


def build_evidence_digest(text: str, risk_terms: Dict[str, str]) -> Dict[str, Any]:
    """
    Build a compact, token-budgeted digest of the risk factors section,
    organized by category, instead of a blind character slice.
    """
    per_category_snippets: Dict[str, List[str]] = {}
    match_counts: Dict[str, int] = {}

    for category, pattern in risk_terms.items():
        all_matches = re.findall(pattern, text, flags=re.IGNORECASE)
        match_counts[category] = len(all_matches)
        per_category_snippets[category] = _get_snippets(
            text, pattern, SNIPPET_WINDOW, MAX_SNIPPETS_PER_CATEGORY
        )

    matched_categories = [c for c, n in match_counts.items() if n > 0]

    # Allocate the char budget evenly across categories that actually matched
    budget = _char_budget()
    truncated = False
    digest_parts = []

    if matched_categories:
        per_category_budget = budget // len(matched_categories)
        for category in matched_categories:
            snippets = per_category_snippets[category]
            block = f"[{category.upper()}]\n" + "\n---\n".join(snippets)
            if len(block) > per_category_budget:
                block = block[:per_category_budget].rsplit(" ", 1)[0] + " ...[truncated]"
                truncated = True
            digest_parts.append(block)
        digest = "\n\n".join(digest_parts)
    else:
        # No keyword matches at all — fall back to a plain head slice,
        # but flag it clearly so downstream steps know it's a weak signal.
        digest = text[:budget]
        truncated = len(text) > budget

    return {
        "digest": digest,
        "matched_categories": matched_categories,
        "match_counts": match_counts,
        "truncated": truncated,
        "fallback_used": not matched_categories,
    }


def check_risk_factors_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    """Screen Item 1A and build an LLM-ready evidence digest, not a blind slice."""
    text = state.get("risk_factors") or ""

    if not text:
        return {
            "risk_assessment": {
                "matched_categories": [],
                "match_counts": {c: 0 for c in RISK_TERMS},
                "evidence_available": False,
                "llm_input": "",
                "truncated": False,
            }
        }

    result = build_evidence_digest(text, RISK_TERMS)

    return {
        "risk_assessment": {
            "matched_categories": result["matched_categories"],
            "match_counts": result["match_counts"],
            "evidence_available": True,
            "llm_input": result["digest"],
            "truncated": result["truncated"],
            "fallback_used": result["fallback_used"],
        }
    }