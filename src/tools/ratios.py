from typing import Any, Dict


def _year_over_year_growth(current: Any, prior: Any) -> float | None:
    """Return percentage growth when a valid comparative period exists."""
    if current is None or prior is None:
        return None

    current_value = float(current)
    prior_value = float(prior)
    if prior_value == 0:
        return None
    return round(((current_value - prior_value) / abs(prior_value)) * 100, 2)

def calculate_financial_ratios(data: Dict[str, Any]) -> Dict[str, float]:
    """Calculates key solvency, profitability, and liquidity ratios deterministically."""
    revenue = float(data.get("revenue") or 0.0)
    net_income = float(data.get("net_income") or 0.0)
    gross_profit = float(data.get("gross_profit") or 0.0)
    total_assets = float(data.get("total_assets") or 0.0)
    total_liabilities = float(data.get("total_liabilities") or 0.0)
    current_assets = float(data.get("current_assets") or 0.0)
    current_liabilities = float(data.get("current_liabilities") or 0.0)

    # Safe denominator calculations
    equity = total_assets - total_liabilities
    
    metrics: Dict[str, Any] = {
        "net_profit_margin_pct": round((net_income / revenue) * 100, 2) if revenue > 0 else 0.0,
        "gross_margin_pct": round((gross_profit / revenue) * 100, 2) if revenue > 0 else 0.0,
        "current_ratio": round(current_assets / current_liabilities, 2) if current_liabilities > 0 else 0.0,
        "debt_to_equity_ratio": round(total_liabilities / equity, 2) if equity > 0 else 0.0
    }

    metrics["revenue_growth_yoy_pct"] = _year_over_year_growth(
        data.get("revenue"), data.get("revenue_previous")
    )
    metrics["net_income_growth_yoy_pct"] = _year_over_year_growth(
        data.get("net_income"), data.get("net_income_previous")
    )
    return metrics