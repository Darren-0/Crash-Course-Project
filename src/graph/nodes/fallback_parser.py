# src/graph/nodes/fallback_parser.py
from typing import Dict, Any
from src.graph.state import FinancialAnalysisState

def fallback_parser_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    """Fail closed when the filing does not contain required fields."""
    errors = list(state.get("errors", []) or [])
    errors.append("Required SEC/XBRL fields are missing; memo synthesis was blocked.")
    return {
        "validation_status": "FETCH_FAILED",
        "errors": errors
    }

def handle_error_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    """Terminal error node: Synthesizes a structured error report when retrieval fails."""
    err_list = state.get("errors", [])
    error_msg = "\n- ".join(err_list) if err_list else "Unknown error encountered."
    return {
        "final_memo": f"Due Diligence Pipeline Aborted for {state.get('ticker')}.\nErrors:\n- {error_msg}"
    }