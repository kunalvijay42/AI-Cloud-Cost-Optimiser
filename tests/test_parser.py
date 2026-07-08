import unittest

from backend.parser import parse_and_normalize_bill


class ParseAndNormalizeBillTests(unittest.TestCase):
    def test_parse_and_normalize_bill_matches_aws_headers_case_insensitively(self):
        csv_data = (
            "ProductName,UsageQuantity,BlendedCost,ResourceId,Region,Date\n"
            "EC2 Compute,100,125.50,i-abc123,us-east-1,2026-01-01\n"
        ).encode("utf-8")

        result = parse_and_normalize_bill(csv_data, "sample.csv")

        self.assertEqual(result["provider"], "aws")
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["rows"][0]["service_name"], "EC2 Compute")
        self.assertEqual(result["rows"][0]["resource_id"], "i-abc123")
        self.assertEqual(result["rows"][0]["cost"], 125.5)
        self.assertEqual(result["rows"][0]["region"], "us-east-1")


if __name__ == "__main__":
    unittest.main()
