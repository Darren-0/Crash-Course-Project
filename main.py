import argparse
from src.graph.builder import create_financial_graph

def run(ticker: str):
    print(f"Running Due Diligence Pipeline for: {ticker}...")
    app = create_financial_graph()
    
    result = app.invoke({
        "ticker": ticker.upper(),
        "raw_filing_summary": None,
        "calculated_metrics": None,
        "risk_factors": None,
        "risk_assessment": None,
        "final_memo": None,
        "validation_status": "",
        "errors": [],
        # New fields for agentic research loop
        "research_log": [],
        "iteration_count": 0
    }, 
        config={"recursion_limit": 100}              
    )
    
    print("\n" + "="*50)
    print("FINANCIAL DUE DILIGENCE MEMO")
    print("="*50 + "\n")
    print(result["final_memo"])
    
    # Optionally print research log for audit trail
    if result.get("research_log"):
        print("\n" + "="*50)
        print("RESEARCH AUDIT LOG")
        print("="*50 + "\n")
        for i, entry in enumerate(result["research_log"], 1):
            print(f"{i}. {entry['tool_name']}")
            print(f"   Input: {entry['tool_input']}")
            print(f"   Timestamp: {entry['timestamp']}")
            print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial Due Diligence Agent")
    parser.add_argument("--ticker", type=str, default="AAPL", help="Company ticker symbol")
    args = parser.parse_args()
    
    run(args.ticker)