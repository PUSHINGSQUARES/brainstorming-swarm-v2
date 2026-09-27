import unittest

from scripts.check_campaign import validate_evidence


class EvidenceContractTests(unittest.TestCase):
    def test_three_anchor_kinds(self):
        self.assertEqual(
            validate_evidence({"kind": "file", "path": "brief.md", "lines": [1, 2]}),
            [],
        )
        self.assertEqual(
            validate_evidence(
                {"kind": "url", "url": "https://example.org/x", "section": "Intro"}
            ),
            [],
        )
        self.assertEqual(validate_evidence({"kind": "supplied", "id": "context-1"}), [])

    def test_anchor_missing_required_location(self):
        self.assertTrue(validate_evidence({"kind": "file", "path": "brief.md"}))
        self.assertTrue(validate_evidence({"kind": "url", "url": "https://example.org/x"}))


if __name__ == "__main__":
    unittest.main()
