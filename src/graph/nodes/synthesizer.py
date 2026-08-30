from typing import Dict, Any
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from src.graph.state import FinancialAnalysisState

# Initialize local Ollama model (no API keys required)
llm = ChatOllama(
    model="llama3.1",
    temperature=0.1
)

def synthesize_memo_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    ticker = state["ticker"]
    metrics = state.get("calculated_metrics", {})
    raw = state.get("raw_filing_summary", {})
    risks = state.get("risk_factors", "None extracted.")
    research_log = state.get("research_log", [])

    system_prompt = (
        "You are a Senior Investment Analyst. You write precise, concise due diligence memos. "
        "Base your analysis strictly on the verified metrics, extracted risk factors, and research evidence provided. "
        "Do not invent or assume numbers. Integrate research findings into your narrative."
    )

    # Build research log summary
    research_summary = ""
    if research_log:
        research_summary = "\nADDITIONAL RESEARCH CONDUCTED:\n"
        for i, entry in enumerate(research_log, 1):
            tool_name = entry.get("tool_name", "unknown")
            tool_input = entry.get("tool_input", {})
            result = entry.get("result", {})
            
            research_summary += f"\n{i}. {tool_name.upper()}\n"
            research_summary += f"   Query: {json.dumps(tool_input)}\n"
            
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                if status == "success":
                    data_summary = str(result.get("data", ""))[:500]
                    research_summary += f"   Status: Success\n"
                    research_summary += f"   Summary: {data_summary}...\n"
                elif status == "error":
                    research_summary += f"   Status: Error - {result.get('error', 'unknown')}\n"
                else:
                    research_summary += f"   Status: {status}\n"
            else:
                research_summary += f"   Result: {str(result)[:200]}\n"

    human_prompt = f"""
Target Entity: {ticker}

VERIFIED FINANCIAL RATIOS (Computed via deterministic code):
- Net Profit Margin: {metrics.get('net_profit_margin_pct', 'N/A')}%
- Gross Margin: {metrics.get('gross_margin_pct', 'N/A')}%
- Current Ratio (Liquidity): {metrics.get('current_ratio', 'N/A')}
- Debt-to-Equity Ratio: {metrics.get('debt_to_equity_ratio', 'N/A')}
- Revenue Growth YoY: {metrics.get('revenue_growth_yoy_pct', 'N/A')}%
- Net Income Growth YoY: {metrics.get('net_income_growth_yoy_pct', 'N/A')}%

RAW BALANCE SHEET & INCOME HIGHLIGHTS:
{raw}

EXTRACTED ITEM 1A RISK FACTORS:
{risks}

RISK SCREENING RESULT:
{state.get('risk_assessment', {})}{research_summary}

Generate a concise 3-part memo:
1. Financial Health & Ratio Assessment
2. Key Material Risk Analysis (incorporate any research findings)
3. Final Due Diligence Recommendation & Next Steps
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    return {"final_memo": response.content}