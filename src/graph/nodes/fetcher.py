# src/graph/nodes/fetcher.py
import re
from typing import Any, Dict
from edgar import Company, set_identity
from src.graph.state import FinancialAnalysisState

set_identity("DueDiligenceBot admin@localresearch.internal")

def fetch_sec_filing_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    ticker = state["ticker"]
    try:
        company = Company(ticker)
        filings = company.get_filings(form="10-K")
        if not filings:
            return {
                "validation_status": "FETCH_FAILED",
                "errors": [f"No 10-K filings found for {ticker}"]
            }

        latest_filing = filings.latest(1)
        tenk = latest_filing.obj()

        # In modern edgartools, access statements via tenk.income_statement or financials.income_statement
        try:
            financials = tenk.financials
            income_stmt = financials.income_statement().to_dataframe()
            balance_sheet = financials.balance_sheet().to_dataframe()
        except Exception:
            # Fallback direct access if available
            income_stmt = tenk.income_statement().to_dataframe()
            balance_sheet = tenk.balance_sheet().to_dataframe()

        # Helper to extract a value across possible accounting line-item labels
        def get_values(df, candidate_keys):
            date_columns = [
                column for column in df.columns
                if re.match(r"^\d{4}-\d{2}-\d{2}", str(column))
            ]
            candidate_keys = {key.lower() for key in candidate_keys}
            for _, row in df.iterrows():
                labels = {
                    str(row.get(column, "")).lower()
                    for column in ("concept", "standard_concept", "label")
                }
                if not labels.isdisjoint(candidate_keys):
                    values = []
                    for column in date_columns[:2]:
                        try:
                            values.append(float(row[column]))
                        except (ValueError, TypeError):
                            values.append(None)
                    return values
            return []

        def current_value(values):
            return values[0] if values else None

        def prior_value(values):
            return values[1] if len(values) > 1 else None

        revenue = get_values(income_stmt, ["Revenue", "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "TotalRevenuesAndOtherIncome"])
        net_income = get_values(income_stmt, ["NetIncomeLoss", "ProfitLoss", "NetIncome"])
        gross_profit = get_values(income_stmt, ["GrossProfit", "GrossMargin"])
        total_assets = get_values(balance_sheet, ["Assets", "TotalAssets"])
        total_liabilities = get_values(balance_sheet, ["Liabilities", "TotalLiabilities", "LiabilitiesAndStockholdersEquity"])
        current_assets = get_values(balance_sheet, ["AssetsCurrent", "CurrentAssets", "CurrentAssetsTotal", "Total current assets"])
        current_liabilities = get_values(balance_sheet, ["LiabilitiesCurrent", "CurrentLiabilities", "CurrentLiabilitiesTotal", "Total current liabilities"])

        raw_data = {
            "revenue": current_value(revenue), "revenue_previous": prior_value(revenue),
            "net_income": current_value(net_income), "net_income_previous": prior_value(net_income),
            "gross_profit": current_value(gross_profit),
            "total_assets": current_value(total_assets),
            "total_liabilities": current_value(total_liabilities),
            "current_assets": current_value(current_assets),
            "current_liabilities": current_value(current_liabilities),
        }

        try:
            risk_text = getattr(tenk, "risk_factors", None)
            risk_factors_found = bool(risk_text)
        except Exception as e:
            risk_text = None
            risk_factors_found = False

        risk_factors_full = str(risk_text) if risk_text else ""

        # Determine validation status
        required_fields = ["revenue", "net_income", "gross_profit", "total_assets",
                            "total_liabilities", "current_assets", "current_liabilities"]
        missing_fields = [k for k in required_fields if raw_data[k] is None]

        status = "VALID"
        if missing_fields:
            status = "MISSING_FIELDS"
        if not risk_factors_found:
            status = "MISSING_RISK_FACTORS" if status == "VALID" else status

        return {
            "raw_filing_summary": raw_data,
            "risk_factors": risk_factors_full,          # full text, no truncation here
            "validation_status": status,
            "errors": (
                [f"Missing XBRL fields: {', '.join(missing_fields)}"] if missing_fields else []
            ) + ([] if risk_factors_found else ["Risk factors section not retrieved"]),
        }

    except Exception as e:
        return {
            "validation_status": "FETCH_FAILED",
            "errors": [f"SEC Retrieval Exception: {str(e)}"]
        }