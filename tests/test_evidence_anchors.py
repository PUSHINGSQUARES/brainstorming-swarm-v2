import json
import unittest

from scripts.check_campaign import validate_campaign, validate_evidence
from tests.test_checker import CampaignCase


class EvidenceTests(CampaignCase):
    def test_all_three_kinds(self):
        for value in (
            {"kind": "file", "path": "sources/brief.md", "lines": [1, 3]},
            {"kind": "url", "url": "https://example.org/x", "section": "Overview"},
            {"kind": "supplied", "id": "context-1"},
        ):
            self.assertEqual(validate_evidence(value), [])

    def test_missing_and_unsupported_anchor(self):
        self.assertIn("evidence.lines is required", validate_evidence({"kind": "file", "path": "x"}))
        self.assertIn("evidence.section is required", validate_evidence({"kind": "url", "url": "https://example.org"}))
        self.assertIn("evidence.kind", " ".join(validate_evidence({"kind": "other"})))
        self.assertIn("evidence.kind", " ".join(validate_evidence({"kind": []})))

    def test_missing_local_evidence_file(self):
        digest_path = self.root / "digests" / "g1.json"
        digest = json.loads(digest_path.read_text())
        digest["findings"][0]["evidence"]["path"] = "sources/absent.md"
        digest_path.write_text(json.dumps(digest))
        self.assertIn("missing evidence file", " ".join(validate_campaign(self.root)))


if __name__ == "__main__":
    unittest.main()
