import unittest

from src.graph.builder import route_after_fetch
from src.graph.nodes.fallback_parser import fallback_parser_node
from src.graph.nodes.risk_checker import check_risk_factors_node


class GraphFlowTests(unittest.TestCase):
	def test_missing_fields_route_to_fail_closed_handler(self):
		self.assertEqual(route_after_fetch({"validation_status": "MISSING_FIELDS"}), "fallback_parser")
		result = fallback_parser_node({"errors": ["Missing gross_profit"]})
		self.assertEqual(result["validation_status"], "FETCH_FAILED")
		self.assertNotIn("raw_filing_summary", result)

	def test_risk_checker_keeps_categories_and_source_excerpt(self):
		text = "The company faces liquidity pressure and debt covenant risk."
		result = check_risk_factors_node({"risk_factors": text})
		assessment = result["risk_assessment"]
		self.assertEqual(assessment["matched_categories"], ["liquidity", "leverage"])
		self.assertEqual(assessment["source_excerpt"], text)


if __name__ == "__main__":
	unittest.main()
