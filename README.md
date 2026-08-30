# Crash-Course-Project

Autonomous financial due diligence over SEC 10-K filings using LLM-driven research agent.

## Overview

This project implements a **LangGraph-based financial research pipeline** that automatically analyzes public companies through an intelligent agent that decides which research tools to call. The agent examines SEC filings, extracts financial metrics, analyzes risks, gathers market intelligence, and synthesizes findings into an investment memo.

## Architecture

### Core Components

1. **State Management** - Central `FinancialAnalysisState` carries data through the pipeline
2. **SEC Filing Node** - Fetches latest 10-K using edgartools
3. **Math Engine** - Calculates deterministic financial ratios
4. **Risk Checker** - Extracts and analyzes risk factors from Item 1A
5. **Research Agent** - LLM-driven decision maker that selects which tools to call
6. **Tool Executor** - Executes research tools and logs results to audit trail
7. **Synthesizer** - Generates final investment memo consuming research log
8. **Router & Guardrails** - Controls loop flow with iteration limits and termination logic

### Research Tools (Agent-Callable)

The agent can select from 5 specialized research tools:

| Tool | Input | Output |
|------|-------|--------|
| **fetch_filing_section** | ticker, section | Text from 10-K (business, risk_factors, md_a, legal) |
| **get_peer_financials** | ticker | Peer companies filtered by market cap, with metrics |
| **get_analyst_estimates** | ticker | Consensus rating, target price, EPS estimates |
| **search_news** | ticker, topic | Recent news articles matching topic |
| **extract_financial_metrics** | ticker | Financial ratios ready for calculation |

### Tool Implementation Details

#### get_peer_financials (Market Cap Filtered)
- **Sector Mapping**: Curated peer lists across 10 sectors (Technology, Healthcare, Finance, etc.)
- **Market Cap Filtering**: Only includes peers within 0.5x to 2x target company's market cap
- **Metrics Returned**: P/E ratio, P/B ratio, dividend yield, revenue, net income, margins (gross/operating/profit), current ratio, debt-to-equity
- **Uses**: yfinance for real-time market data

#### get_analyst_estimates
- **Source**: yfinance aggregated analyst data
- **Consensus Rating**: Strong Buy/Buy/Hold/Sell/Strong Sell
- **Target Price**: Mean analyst price target
- **Upside/Downside**: Percentage return to target
- **EPS Data**: Current EPS, forward EPS, growth estimates

#### search_news
- **Source**: yfinance news feed
- **Filtering**: Keyword matching on topic in title/summary
- **Fallback**: Returns 5 most recent articles if no topic match
- **Data**: Title, source, date, summary (capped at 300 chars)

## Workflow

The active LangGraph workflow is:

1. **Fetch** the latest 10-K with edgartools
2. **Normalize** income statement and balance sheet values
3. **Calculate** margins, liquidity, leverage, and YoY growth
4. **Screen** risk factors from Item 1A
5. **Research Agent Decides**: Based on current state, agent picks which tools to call (0-2 iterations)
6. **Execute Tools**: Agent's selected tools run, results logged to research audit trail
7. **Synthesis**: LLM writes investment memo consuming all gathered data
8. **Output**: Investment memo + complete research audit log

### Loop Control & Guardrails

- **Max Iterations**: 2 iterations (early exit prevents infinite loops)
- **Termination Signals**: Agent declares "finish" when sufficient data gathered
- **Recursion Limit**: 100 (prevents LangGraph stack overflow)

## Run

Install dependencies into the project virtual environment, start Ollama with the `gemma4:cloud` model, then run:

```powershell
python main.py --ticker AAPL
```

### Expected Output

1. **Investment Memo**: Comprehensive due diligence analysis with financial assessment, risk analysis, and recommendations
2. **Research Audit Trail**: Complete log of all tool calls with inputs, timestamps, and results

### Run Tests

```powershell
python -m unittest discover -s tests -v
```

## Project Structure

```
src/
├── graph/
│   ├── builder.py          # LangGraph workflow construction
│   ├── state.py            # State schema definition
│   └── nodes/              # Individual pipeline nodes
│       ├── fetcher.py      # SEC filing fetcher
│       ├── math_engine.py  # Financial calculations
│       ├── risk_checker.py # Risk extraction
│       ├── agent_node.py   # Research agent (LLM)
│       ├── tool_executor_node.py  # Tool router
│       ├── synthesizer.py  # Memo generator
│       └── fallback_parser.py # Error handling
├── tools/
│   └── research_tools.py   # Tool implementations
└── mcp/                    # Reserved for future MCP integrations
```

## Technology Stack

- **LangGraph**: Agentic workflow orchestration
- **LangChain**: LLM framework and utilities
- **ChatOllama**: Local inference with Gemma model (no API keys)
- **yfinance**: Market data and analyst consensus
- **edgartools**: SEC EDGAR filing extraction
- **Pydantic**: Type validation
- **Pandas**: Data manipulation

## Future Enhancements

- Integration with additional data providers (Bloomberg, Refinitiv, Capital IQ)
- Enhanced peer selection using SIC code classification
- Real news API integration (NewsAPI, Bloomberg, etc.)
- Machine learning for risk scoring
- Portfolio-level analysis
- MCP server integration for extended toolset

## Notes

- The `src/mcp` folder is reserved for future integrations and is not part of the current production path.
- All LLM reasoning uses local Ollama inference (no external API dependencies).
- The research audit trail provides full transparency into agent decision-making.