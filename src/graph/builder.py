from typing import Literal
from langgraph.graph import StateGraph, START, END
from src.graph.state import FinancialAnalysisState
from src.graph.nodes.fetcher import fetch_sec_filing_node
from src.graph.nodes.fallback_parser import fallback_parser_node, handle_error_node
from src.graph.nodes.math_engine import deterministic_math_node
from src.graph.nodes.synthesizer import synthesize_memo_node
from src.graph.nodes.risk_checker import check_risk_factors_node
from src.graph.nodes.agent_node import research_agent_node
from src.graph.nodes.tool_executor_node import tool_executor_node

# Configuration for research loop guardrails
MAX_RESEARCH_ITERATIONS = 5

def route_after_fetch(state: FinancialAnalysisState) -> Literal["calculate_math", "fallback_parser", "handle_error"]:
    """Conditional routing function inspecting the state status."""
    status = state.get("validation_status")
    if status == "VALID":
        return "calculate_math"
    elif status == "MISSING_FIELDS":
        return "fallback_parser"
    return "handle_error"

def route_research_decision(state: FinancialAnalysisState) -> Literal["research_agent", "synthesize_memo"]:
    """
    Guardrail: decide whether to continue research or move to synthesis.
    
    Routes to synthesis if:
    1. Agent decided to finish research, OR
    2. Maximum iteration count reached
    
    Otherwise, routes back to the research agent.
    """
    agent_output = state.get("agent_output", {})
    agent_decision = agent_output.get("agent_decision", "")
    iteration_count = state.get("iteration_count", 0)
    
    print(f"[ROUTER] Iteration: {iteration_count}, Agent Decision: {agent_decision}")
    
    # Force exit at max iterations
    if iteration_count >= MAX_RESEARCH_ITERATIONS:
        print(f"[ROUTER] Max iterations ({MAX_RESEARCH_ITERATIONS}) reached → synthesizing")
        return "synthesize_memo"
    
    # Exit if agent finished
    if agent_decision == "finish":
        print(f"[ROUTER] Agent finished research → synthesizing")
        return "synthesize_memo"
    
    # Continue research
    print(f"[ROUTER] Continuing research loop")
    return "research_agent"

def create_financial_graph():
    workflow = StateGraph(FinancialAnalysisState)

    # Register Nodes
    workflow.add_node("fetch_sec", fetch_sec_filing_node)
    workflow.add_node("fallback_parser", fallback_parser_node)
    workflow.add_node("calculate_math", deterministic_math_node)
    workflow.add_node("check_risks", check_risk_factors_node)
    workflow.add_node("research_agent", research_agent_node)
    workflow.add_node("execute_tools", tool_executor_node)
    workflow.add_node("synthesize_memo", synthesize_memo_node)
    workflow.add_node("handle_error", handle_error_node)

    # Base Edges
    workflow.add_edge(START, "fetch_sec")

    # Conditional Branching from Fetcher
    workflow.add_conditional_edges(
        "fetch_sec",
        route_after_fetch,
        {
            "calculate_math": "calculate_math",
            "fallback_parser": "fallback_parser",
            "handle_error": "handle_error"
        }
    )

    # Reconnect Fallback back into standard pipeline
    workflow.add_edge("fallback_parser", "handle_error")
    
    # Main pipeline to research loop
    workflow.add_edge("calculate_math", "check_risks")
    workflow.add_edge("check_risks", "research_agent")
    
    # Research loop with guardrails
    workflow.add_edge("research_agent", "execute_tools")
    workflow.add_conditional_edges(
        "execute_tools",
        route_research_decision,
        {
            "research_agent": "research_agent",  # Loop back to agent if more research needed
            "synthesize_memo": "synthesize_memo"
        }
    )
    
    # Terminal Edges
    workflow.add_edge("synthesize_memo", END)
    workflow.add_edge("handle_error", END)

    return workflow.compile()