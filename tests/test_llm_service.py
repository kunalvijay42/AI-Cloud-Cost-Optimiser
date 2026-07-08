import unittest
from unittest.mock import patch

from backend.llm_service import generate_suggestions


class GenerateSuggestionsTests(unittest.TestCase):
    @patch("backend.llm_service.requests.post", side_effect=Exception("boom"))
    def test_generate_suggestions_returns_fallback_when_request_fails(self, _mock_post):
        stats = {
            "provider": "aws",
            "stats": {
                "total_cost": 150.0,
                "cost_by_service": {"EC2": 100.0},
                "cost_by_region": {"us-east-1": 100.0},
                "top_expenses": [{"resource_id": "i-123", "cost": 100.0}],
            },
        }

        suggestions = generate_suggestions(stats)

        self.assertIsInstance(suggestions, list)
        self.assertGreaterEqual(len(suggestions), 1)
        self.assertIn("suggestion", suggestions[0])
        self.assertIn("affected_resource", suggestions[0])
        self.assertIn("priority", suggestions[0])
        self.assertIn("Rightsize", suggestions[0]["suggestion"])


if __name__ == "__main__":
    unittest.main()
