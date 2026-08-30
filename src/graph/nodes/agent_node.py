"""
Research agent node that decides which tools to call during investigation.
Uses qgemma4:cloud model via Ollama for reasoning.
"""

import json
from typing import Any, Dict
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from src.graph.state import FinancialAnalysisState
from src.tools.research_tools import ToolExecutor


# Initialize Qwen model via Ollama
llm = ChatOllama(
    model="gemma4:cloud",  # User's specified model
    temperature=0.5,   # Balance exploration with consistency
    top_p=0.9
)

# Bind tools to the LLM
research_tools_definitions = ToolExecutor.get_tool_definitions()


def research_agent_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    """
    Research agent that examines the current state and evidence,
    then decides: call a tool for more research, or declare research complete.
    
    Returns a dict with:
    - tool_calls: list of tools to execute, OR
    - finish: True if research is complete
    - reasoning: why this decision was made
    """
    
    ticker = state.get("ticker", "UNKNOWN")
    research_log = state.get("research_log", [])
    iteration_count = state.get("iteration_count", 0)
    metrics = state.get("calculated_metrics", {})
    raw_filing = state.get("raw_filing_summary", {})
    risk_factors = state.get("risk_factors", "")
    
    # EARLY EXIT: Force finish at iteration 2+ to prevent infinite loops
    if iteration_count >= 2:
        print(f"[AGENT] Forced finish at iteration {iteration_count}")
        return {
            "agent_output": {
                "agent_decision": "finish",
                "reasoning": f"Research depth limit reached at iteration {iteration_count}",
                "tool_calls": []
            }
        }
    
    # Build a summary of what we know so far
    evidence_summary = f"""
CURRENT RESEARCH STATE FOR {ticker}:

Research Iterations Completed: {iteration_count}

DATA GATHERED SO FAR:
- Raw Filing Summary: {bool(raw_filing)}
- Calculated Metrics: {bool(metrics)}
- Risk Factors Extracted: {bool(risk_factors)}
- Previous Tool Calls: {len(research_log)}

RESEARCH LOG:
"""
    
    if research_log:
        for i, entry in enumerate(research_log, 1):
            evidence_summary += f"\n{i}. Tool: {entry['tool_name']}\n"
            evidence_summary += f"   Input: {json.dumps(entry.get('tool_input', {}), indent=2)}\n"
            evidence_summary += f"   Result Summary: {_summarize_result(entry.get('result', {}))}\n"
    else:
        evidence_summary += "\n(No previous tool calls yet)"
    
    system_prompt = f"""You are a Senior Investment Research Agent conducting due diligence on {ticker}.

Your role is to decide intelligently which research tools to call next, based on:
1. What data you've already gathered
2. What gaps remain for a thorough analysis
3. The specific company and market conditions

AVAILABLE TOOLS AND EXACT PARAMETERS:

1. fetch_filing_section
   Required params: company (ticker symbol), item (section name: "risk_factors", "business", "md_a", or "legal")
   Example: {{"tool": "fetch_filing_section", "args": {{"company": "{ticker}", "item": "business"}}}}

2. search_news
   Required params: company (name or ticker), topic (search topic)
   Example: {{"tool": "search_news", "args": {{"company": "{ticker}", "topic": "earnings"}}}}

3. get_peer_financials
   Required params: ticker (company ticker symbol)
   Example: {{"tool": "get_peer_financials", "args": {{"ticker": "{ticker}"}}}}

4. get_analyst_estimates
   Required params: ticker (company ticker symbol)
   Example: {{"tool": "get_analyst_estimates", "args": {{"ticker": "{ticker}"}}}}

5. extract_financial_metrics
   Required params: ticker (company ticker symbol)
   Example: {{"tool": "extract_financial_metrics", "args": {{"ticker": "{ticker}"}}}}

DECISION LOGIC:
- If you have basic metrics, risk factors, and business overview → declare FINISH
- If critical data is missing (e.g., no risk assessment yet) → call fetch_filing_section
- If financials need peer comparison → call get_peer_financials
- If synthesis might need external validation → call search_news or get_analyst_estimates
- Prioritize depth in key areas over breadth

Respond with EITHER:
1. A JSON array of tool calls (use EXACT parameter names from examples above)
2. The word FINISH if research is complete

CRITICAL: Use parameter names exactly as shown. Do NOT use "ticker" when "company" is required, and vice versa."""

    human_prompt = f"""{evidence_summary}

Based on the current state and evidence above, analyze what research gaps remain and respond with:

EITHER (if more research is needed):
- A JSON array with tool calls using EXACT parameter names
- Example: [
    {{"tool": "fetch_filing_section", "args": {{"company": "{ticker}", "item": "risk_factors"}}}},
    {{"tool": "get_peer_financials", "args": {{"ticker": "{ticker}"}}}}
  ]

OR (if research is complete):
- Simply respond with: FINISH

Key reminders:
- Use "company" parameter for fetch_filing_section and search_news
- Use "ticker" parameter for get_peer_financials, get_analyst_estimates, extract_financial_metrics
- Use "item" parameter (not "section") for fetch_filing_section
- Respond with valid JSON or the word FINISH - nothing else"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        response_text = response.content.strip()
        
        iteration_count = state.get("iteration_count", 0)
        
        # Parse the response
        if "FINISH" in response_text.upper() or response_text.upper() == "FINISH":
            return {
                "agent_output": {
                    "agent_decision": "finish",
                    "reasoning": response_text,
                    "tool_calls": []
                }
            }
        
        # Try to parse as JSON tool calls
        try:
            # Extract JSON from the response (handle markdown code blocks)
            if "```" in response_text:
                json_str = response_text.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            else:
                json_str = response_text
            
            tool_calls = json.loads(json_str)
            
            # Validate tool_calls format
            if isinstance(tool_calls, list):
                validated_calls = []
                for call in tool_calls:
                    if isinstance(call, dict) and "tool" in call and "args" in call:
                        validated_calls.append(call)
                
                if validated_calls:
                    return {
                        "agent_output": {
                            "agent_decision": "continue",
                            "reasoning": f"Executing {len(validated_calls)} tool(s)",
                            "tool_calls": validated_calls
                        }
                    }
        except (json.JSONDecodeError, ValueError):
            pass
        
        # If all else fails, assume we should finish
        # (Don't keep trying to extract tools - this causes infinite loops)
        print(f"[AGENT] Could not parse response clearly, finishing research")
        return {
            "agent_output": {
                "agent_decision": "finish",
                "reasoning": f"Could not parse agent decision: {response_text[:200]}",
                "tool_calls": []
            }
        }
    
    except Exception as e:
        return {
            "agent_output": {
                "agent_decision": "error",
                "reasoning": f"Error in agent reasoning: {str(e)}",
                "tool_calls": [],
                "error": str(e)
            }
        }


def _summarize_result(result: Any) -> str:
    """Summarize a tool result for the research log."""
    if isinstance(result, dict):
        status = result.get("status", "unknown")
        if status == "success":
            return f"Success - {len(str(result.get('data', '')))} chars retrieved"
        elif status == "error":
            return f"Error: {result.get('error', 'unknown')}"
        else:
            return f"Status: {status}"
    return str(result)[:100]
