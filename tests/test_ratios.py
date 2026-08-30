import unittest

from src.tools.ratios import calculate_financial_ratios


class RatioTests(unittest.TestCase):
	def test_calculates_margins_liquidity_leverage_and_growth(self):
		metrics = calculate_financial_ratios({
			"revenue": 120,
			"revenue_previous": 100,
			"net_income": 15,
			"net_income_previous": 10,
			"gross_profit": 48,
			"total_assets": 200,
			"total_liabilities": 100,
			"current_assets": 80,
			"current_liabilities": 40,
		})

		self.assertEqual(metrics["net_profit_margin_pct"], 12.5)
		self.assertEqual(metrics["gross_margin_pct"], 40.0)
		self.assertEqual(metrics["current_ratio"], 2.0)
		self.assertEqual(metrics["debt_to_equity_ratio"], 1.0)
		self.assertEqual(metrics["revenue_growth_yoy_pct"], 20.0)
		self.assertEqual(metrics["net_income_growth_yoy_pct"], 50.0)

	def test_growth_is_unavailable_without_comparative_period(self):
		metrics = calculate_financial_ratios({
			"revenue": 120,
			"net_income": 15,
			"gross_profit": 48,
			"total_assets": 200,
			"total_liabilities": 100,
			"current_assets": 80,
			"current_liabilities": 40,
		})

		self.assertIsNone(metrics["revenue_growth_yoy_pct"])
		self.assertIsNone(metrics["net_income_growth_yoy_pct"])


if __name__ == "__main__":
	unittest.main()
