"""
Tool execution node that runs the tools selected by the research agent.
Appends results to the research_log in the state.
"""

from typing import Any, Dict
from datetime import datetime
from src.graph.state import FinancialAnalysisState, ResearchLogEntry
from src.tools.research_tools import ToolExecutor


def tool_executor_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    """
    Execute the tools selected by the agent and log results.
    
    Expects state to contain agent_tool_calls from the previous node.
    Updates research_log and increments iteration_count.
    """
    
    agent_output = state.get("agent_output", {})
    tool_calls = agent_output.get("tool_calls", [])
    research_log = state.get("research_log", []).copy()
    
    if not tool_calls:
        # No tools to execute
        return {
            "research_log": research_log,
            "iteration_count": state.get("iteration_count", 0),
            "agent_output": agent_output
        }
    
    # Execute each tool
    for tool_call in tool_calls:
        tool_name = tool_call.get("tool")
        tool_args = tool_call.get("args", {})
        
        try:
            result = ToolExecutor.execute_tool(tool_name, tool_args)
            
            # Create log entry
            log_entry: ResearchLogEntry = {
                "tool_name": tool_name,
                "tool_input": tool_args,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            research_log.append(log_entry)
        
        except Exception as e:
            # Log the error
            log_entry: ResearchLogEntry = {
                "tool_name": tool_name,
                "tool_input": tool_args,
                "result": {
                    "status": "execution_error",
                    "error": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            research_log.append(log_entry)
    
    return {
        "research_log": research_log,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "agent_output": agent_output
    }
