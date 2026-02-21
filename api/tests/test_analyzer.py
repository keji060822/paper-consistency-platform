import unittest
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.services.analyzer import analyze_text


class AnalyzerTests(unittest.TestCase):
    def test_detects_multiple_inconsistency_types(self) -> None:
        text = (
            "We name this metric threshold voltage window. "
            "Later we rename the same metric switching threshold bandwidth with a different definition. "
            "Section 2 says higher temperature improves robustness. "
            "Section 3 says higher temperature reduces robustness. "
            "Figure 4 in the main text claims improved robustness, but the caption says reduced robustness."
        )

        result = analyze_text(text)
        issue_types = {item["type"] for item in result["issues"]}

        self.assertIn("term", issue_types)
        self.assertIn("logic", issue_types)
        self.assertIn("citation_figure", issue_types)
        self.assertGreaterEqual(len(result["sentences"]), 5)


if __name__ == "__main__":
    unittest.main()
