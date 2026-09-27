import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_campaign import LIMITS, main, validate_campaign


class SoloCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "digests").mkdir()
        (self.root / "LEDGER.md").write_text("# Invented Solo Design\n")
        self.campaign = {
            "campaign_id": "toy-solo",
            "status": "solo_analysis",
            "roles": [{
                "leg_id": "d1", "role": "draft", "host": "example-host",
                "model": "session-default", "effort": "session-default",
                "source_of_choice": "session", "required": False,
                "observed_availability": "available", "routing_reason": "Solo sketch",
                "artifact": "digests/d1.json", "status": "accepted",
            }],
            "approaches": [{"approach_id": "a1", "author_leg_id": "d1"}],
            "synthesis": {"accepted_leg_ids": ["d1"], "selected_approach_id": "a1"},
            "ledger": "LEDGER.md",
        }
        self.digest = {
            "leg_id": "d1", "role": "draft", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "artifact": "digests/d1.json", "approach_id": "a1", "author_leg_id": "d1",
            "revision": 1, "supersedes": None, "title": "Solo signage sketch",
            "central_assumption": "The sign can fit one wall.",
            "proposal": "Use one panel.", "evidence": [], "dependencies": [], "risks": [],
            "rough_effort": "One layout study.", "falsifying_test": "A fitting test shows the panel cannot fit.",
        }
        self.save()

    def save(self):
        (self.root / "campaign.json").write_text(json.dumps(self.campaign))
        (self.root / "digests" / "d1.json").write_text(json.dumps(self.digest))

    def test_solo_without_judge_passes_with_limits(self):
        self.assertEqual(validate_campaign(self.root), [])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("solo_analysis", output.getvalue())
        self.assertIn("Independent agents and judges did not run", output.getvalue())
        self.assertIn(LIMITS, output.getvalue())

    def test_normal_status_still_needs_judge(self):
        self.campaign["status"] = "design_pending"
        self.save()
        self.assertIn("approach a1 incomplete", " ".join(validate_campaign(self.root)))

    def test_solo_cannot_claim_accepted_judge(self):
        self.campaign["roles"].append({
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "source_of_choice": "session", "required": False,
            "observed_availability": "available", "routing_reason": "Claimed independent review",
            "artifact": "digests/j1.json", "status": "accepted",
        })
        (self.root / "digests" / "j1.json").write_text(json.dumps({
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "artifact": "digests/j1.json", "target_id": "a1", "judge_leg_id": "j1",
            "verdict": "keep", "severity": "low", "counterevidence": [],
            "keep_clauses": [],
        }))
        self.save()
        self.assertIn("solo_analysis cannot claim accepted judge", " ".join(validate_campaign(self.root)))

    def test_draft_rejects_malformed_file_anchor(self):
        (self.root / "sources").mkdir()
        (self.root / "sources" / "brief.md").write_text("Invented sign brief.\n")
        self.digest["evidence"] = [{
            "kind": "file", "path": "sources/brief.md", "start_line": 1, "end_line": 1,
        }]
        self.save()
        self.assertIn("draft d1 evidence 0: evidence.lines is required", validate_campaign(self.root))

    def test_draft_rejects_missing_local_evidence_file(self):
        self.digest["evidence"] = [{
            "kind": "file", "path": "sources/absent.md", "lines": [1, 1],
        }]
        self.save()
        self.assertIn("missing evidence file: sources/absent.md", validate_campaign(self.root))

    def test_draft_evidence_must_be_a_list(self):
        del self.digest["evidence"]
        self.save()
        self.assertIn("draft d1 evidence must be a list", validate_campaign(self.root))

    def test_judge_rejects_malformed_counterevidence_anchor(self):
        self.campaign["status"] = "design_pending"
        self.campaign["roles"].append({
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "source_of_choice": "session", "required": False,
            "observed_availability": "available", "routing_reason": "Independent review",
            "artifact": "digests/j1.json", "status": "accepted",
        })
        judge = {
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "artifact": "digests/j1.json", "target_id": "a1", "judge_leg_id": "j1",
            "verdict": "revise", "counterevidence": [{
                "source_fact": "The brief describes a sign.",
                "bearing_on_target": "The draft needs a measured placement before approval.",
                "evidence": {"kind": "file", "path": "sources/brief.md", "start_line": 1, "end_line": 1},
            }],
        }
        (self.root / "sources").mkdir()
        (self.root / "sources" / "brief.md").write_text("Invented sign brief.\n")
        self.save()
        (self.root / "digests" / "j1.json").write_text(json.dumps(judge))
        self.assertIn("judge j1 counterevidence 0: evidence.lines is required", validate_campaign(self.root))

    def test_judge_counterevidence_must_be_a_list(self):
        self.campaign["roles"].append({
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "source_of_choice": "session", "required": False,
            "observed_availability": "available", "routing_reason": "Independent review",
            "artifact": "digests/j1.json", "status": "incomplete",
        })
        self.save()
        (self.root / "digests" / "j1.json").write_text(json.dumps({
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "artifact": "digests/j1.json", "target_id": "a1", "judge_leg_id": "j1",
            "verdict": "revise",
        }))
        self.assertIn("judge j1 counterevidence must be a list", validate_campaign(self.root))

    def add_judge(self, counterevidence, reason=None):
        self.campaign["status"] = "design_pending"
        self.campaign["roles"].append({
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "source_of_choice": "session", "required": False,
            "observed_availability": "available", "routing_reason": "Independent review",
            "artifact": "digests/j1.json", "status": "accepted",
        })
        judge = {
            "leg_id": "j1", "role": "judge", "host": "example-host",
            "model": "session-default", "effort": "session-default",
            "artifact": "digests/j1.json", "target_id": "a1", "judge_leg_id": "j1",
            "verdict": "revise", "counterevidence": counterevidence,
        }
        if reason is not None:
            judge["reason"] = reason
        self.save()
        (self.root / "digests" / "j1.json").write_text(json.dumps(judge))

    def test_judge_reason_required_even_without_counterevidence(self):
        self.add_judge([], reason="  ")
        self.assertIn("judge j1 reason is required", validate_campaign(self.root))

    def test_judge_counterevidence_source_fact_required(self):
        self.add_judge([{"source_fact": " ", "bearing_on_target": "Revise placement.",
                         "evidence": {"kind": "supplied", "id": "toy-brief"}}],
                       reason="Review the invented sign brief.")
        self.assertIn("judge j1 counterevidence 0 source_fact is required", validate_campaign(self.root))


if __name__ == "__main__":
    unittest.main()
