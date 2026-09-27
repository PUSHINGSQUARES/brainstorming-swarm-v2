"""Host guide status must agree with real, linked support evidence."""

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from tests.check_host_guides import validate_guides
from tests.test_release_matrix_expiry import synthetic_receipt


HOSTS = ("Claude", "Codex", "Grok", "Muse")
TARGETS = ("Opus 5.5", "GPT-6 Sol", "Grok 4.7", "Unverified")


class HostGuideTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.guides = self.root / "references" / "host-guides"
        self.guides.mkdir(parents=True)
        self.write_matrix()
        for host in HOSTS:
            self.write_guide(host)

    def write_matrix(self, tested_host=None, receipt="none"):
        lines = ["# Support", "", "| Host | Target model | Status | Host version | Model ID | Probe date | Model control | Effort control | Receipt |",
                 "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for host, target in zip(HOSTS, TARGETS):
            status = "tested" if host == tested_host else "candidate"
            path = receipt if host == tested_host else "none"
            model_id = "gpt-6-sol" if host == tested_host else "model-1"
            lines.append(f"| {host} | {target} | {status} | fixture-1 | {model_id} | 2026-09-26 | available | available | {path} |")
        (self.root / "SUPPORT.md").write_text("\n".join(lines) + "\n")

    def write_guide(self, host, status="candidate", extra="", receipt="none", version="unverified", model="unverified", probe="unverified"):
        text = (f"# {host} Host Guide\n\n## Host Observation\n\n"
                f"| Field | Observation |\n| --- | --- |\n"
                f"| Support status | `{status}` |\n"
                f"| Live host version | {version} |\n"
                f"| Live model ID | {model} |\n"
                f"| Live probe date | {probe} |\n"
                f"| Live receipt | {receipt} |\n\n"
                f"{extra}\n")
        (self.guides / f"{host.lower()}.md").write_text(text)

    def test_honest_candidates_pass(self):
        self.assertEqual(validate_guides(self.root, date(2026, 9, 26)), [])

    def test_missing_guide_fails(self):
        (self.guides / "muse.md").unlink()
        self.assertTrue(validate_guides(self.root, date(2026, 9, 26)))

    def test_candidate_success_claim_fails(self):
        claims = (
            "We successfully spawned two children.",
            "Two children completed successfully and returned independent artifacts.",
            "The children were spawned concurrently and both succeeded.",
            "A live probe confirmed overlapping subagents.",
            "We spawned two independent agents successfully.",
            "Two agents completed successfully and returned separate artifacts.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.write_guide("Codex", extra=claim)
                self.assertTrue(validate_guides(self.root, date(2026, 9, 26)))

    def test_candidate_negated_claims_pass(self):
        for caveat in ("No live probe confirmed overlapping subagents.", "Two children were not spawned."):
            with self.subTest(caveat=caveat):
                self.write_guide("Codex", extra=caveat)
                self.assertEqual(validate_guides(self.root, date(2026, 9, 26)), [])

    def test_candidate_status_mismatch_fails(self):
        self.write_guide("Codex", status="tested")
        self.assertTrue(validate_guides(self.root, date(2026, 9, 26)))

    def make_tested(self):
        self.write_matrix(tested_host="Codex", receipt="evidence/probe.json")
        receipt_path = self.root / "evidence" / "probe.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(synthetic_receipt(self.root)))
        self.write_guide("Codex", status="tested", version="fixture-1", model="gpt-6-sol",
                         probe="2026-09-26", receipt="[Probe](../../evidence/probe.json)")
        return receipt_path

    def test_current_tested_baseline_passes(self):
        self.make_tested()
        self.assertEqual(validate_guides(self.root, date(2026, 9, 26)), [])

    def test_tested_receipt_and_tuple_mutations_fail(self):
        receipt_path = self.make_tested()
        self.assertEqual(validate_guides(self.root, date(2026, 9, 26)), [])
        for changed in (
            {"version": "fixture-2"}, {"model": "other-model"}, {"probe": "2026-09-25"},
            {"receipt": "[Probe](evidence/probe.json)"},
            {"receipt": "evidence/probe.json"},
            {"receipt": f"[Probe]({receipt_path})"},
        ):
            with self.subTest(changed=changed):
                values = {"version": "fixture-1", "model": "gpt-6-sol", "probe": "2026-09-26",
                          "receipt": "[Probe](../../evidence/probe.json)"}
                values.update(changed)
                self.write_guide("Codex", status="tested", **values)
                self.assertTrue(validate_guides(self.root, date(2026, 9, 26)))
        self.write_guide("Codex", status="tested", version="fixture-1", model="gpt-6-sol",
                         probe="2026-09-26", receipt="[Probe](../../evidence/probe.json)")
        receipt_path.unlink()
        self.assertTrue(validate_guides(self.root, date(2026, 9, 26)))

    def test_tested_expiry_fails(self):
        self.make_tested()
        self.assertTrue(validate_guides(self.root, date(2026, 12, 27)))


if __name__ == "__main__":
    unittest.main()
