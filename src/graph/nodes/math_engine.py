from typing import Dict, Any
from src.graph.state import FinancialAnalysisState
from src.tools.ratios import calculate_financial_ratios

def deterministic_math_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    raw_data = state.get("raw_filing_summary")
    if not raw_data:
        return {"errors": ["No raw financial data available to compute ratios."]}

    metrics = calculate_financial_ratios(raw_data)
    return {"calculated_metrics": metrics}