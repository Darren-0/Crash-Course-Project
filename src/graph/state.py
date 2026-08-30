from typing import Any, Dict, Optional, TypedDict

class ResearchLogEntry(TypedDict):
    """A single research action in the log."""
    tool_name: str
    tool_input: Dict[str, Any]
    result: Any
    timestamp: str

class AgentOutput(TypedDict, total=False):
    """Output from the research agent."""
    agent_decision: str  # "continue", "finish", or "error"
    reasoning: str
    tool_calls: list[Dict[str, Any]]
    error: Optional[str]

class FinancialAnalysisState(TypedDict, total=False):
    ticker: str
    raw_filing_summary: Optional[Dict[str, Any]]
    calculated_metrics: Optional[Dict[str, float]]
    risk_factors: Optional[str]
    risk_assessment: Optional[Dict[str, Any]]
    final_memo: Optional[str]
    validation_status: str
    errors: list[str]
    # New fields for agentic research loop
    research_log: list[ResearchLogEntry]
    iteration_count: int
    agent_output: Optional[AgentOutput]