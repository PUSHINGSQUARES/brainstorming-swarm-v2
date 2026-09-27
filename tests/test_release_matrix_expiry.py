"""Disposable synthetic receipts test validation, never public support."""
import copy
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from tests.check_release_matrix import validate_row
from tests.check_live_receipts import validate_receipt


def synthetic_receipt(root, probe_date="2026-09-26"):
    artifacts = []
    for n in (1, 2):
        path = root / "evidence" / ("sample-%s.txt" % n)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Invented artifact %s\n" % n)
        artifacts.append({"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {
        "schema_version": 1, "host": "Codex", "host_version": "fixture-1",
        "target_model": "GPT-6 Sol", "model_id": "gpt-6-sol",
        "probe_date": probe_date, "effort_exposed": True,
        "children": [
            {"child_id": "child-a", "start": probe_date + "T10:00:00Z", "end": probe_date + "T10:02:00Z",
             "reported_model_id": "gpt-6-sol", "model_source": "host", "requested_effort": "medium",
             "reported_effort": "medium", "terminal_state": "completed", "artifact": artifacts[0],
             "raw_event_ids": ["evt-starta", "evt-enda"]},
            {"child_id": "child-b", "start": probe_date + "T10:01:00Z", "end": probe_date + "T10:03:00Z",
             "reported_model_id": "gpt-6-sol", "model_source": "host", "requested_effort": "medium",
             "reported_effort": "medium", "terminal_state": "completed", "artifact": artifacts[1],
             "raw_event_ids": ["evt-startb", "evt-endb"]}],
        "lifecycle_probes": [{"kind": kind, "child_id": "child-" + kind,
            "terminal_state": "termination_unknown", "raw_event_ids": ["evt-" + kind]}
            for kind in ("missing", "malformed", "deadline", "cancel")]
    }


class ReleaseMatrixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.today = date(2026, 9, 26)
        self.receipt = synthetic_receipt(self.root)
        self.row = {"host": "Codex", "target_model": "GPT-6 Sol", "status": "tested",
                    "host_version": "fixture-1", "model_id": "gpt-6-sol", "probe_date": "2026-09-26",
                    "model_control": "available", "effort_control": "available", "receipt": "evidence/test.json"}
        self.save()

    def save(self):
        (self.root / self.row["receipt"]).write_text(json.dumps(self.receipt))

    def test_current_exact_tuple_passes(self):
        self.assertEqual(validate_row(self.row, self.root, self.today), [])

    def test_91_days_expired(self):
        old = (self.today - timedelta(days=91)).isoformat()
        self.receipt = synthetic_receipt(self.root, old)
        self.row["probe_date"] = old
        self.save()
        self.assertIn("probe is older than 90 days", validate_row(self.row, self.root, self.today))

    def test_90_days_is_current(self):
        old = (self.today - timedelta(days=90)).isoformat()
        self.receipt = synthetic_receipt(self.root, old)
        self.row["probe_date"] = old
        self.save()
        self.assertEqual(validate_row(self.row, self.root, self.today), [])

    def test_version_mismatch_fails(self):
        self.row["host_version"] = "fixture-2"
        self.assertIn("receipt host_version does not match matrix", validate_row(self.row, self.root, self.today))

    def test_model_mismatch_fails(self):
        self.row["model_id"] = "other-model"
        self.assertIn("receipt model_id does not match matrix", validate_row(self.row, self.root, self.today))

    def test_unlinked_tested_fails(self):
        self.row["receipt"] = "none"
        self.assertTrue(validate_row(self.row, self.root, self.today))

    def test_future_probe_fails(self):
        self.row["probe_date"] = "2026-09-27"
        self.assertIn("probe date is in the future", validate_row(self.row, self.root, self.today))

    def test_receipt_rejections(self):
        mutations = [
            lambda r: r["children"][1].update(child_id="child-a"),
            lambda r: r["children"][1].update(start="2026-09-26T10:02:00Z"),
            lambda r: r["children"][0].update(reported_model_id="other-model"),
            lambda r: r["children"][0].update(model_source="requested"),
            lambda r: r["children"][0].update(reported_effort="low"),
            lambda r: r["children"][0].update(raw_event_ids=[]),
            lambda r: r["children"][0]["artifact"].update(sha256="0" * 64),
            lambda r: r["lifecycle_probes"][0].pop("terminal_state"),
            lambda r: r.update(lifecycle_probes=[]),
            lambda r: r.update(raw_transcript="Not allowed"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                receipt = copy.deepcopy(self.receipt)
                mutate(receipt)
                self.assertTrue(validate_receipt(receipt, self.root))

    def test_children_cannot_share_raw_events(self):
        self.receipt["children"][1]["raw_event_ids"] = self.receipt["children"][0]["raw_event_ids"][:]
        self.assertIn("raw event IDs must be unique across all child and lifecycle records",
                      validate_receipt(self.receipt, self.root))

    def test_lifecycle_cannot_reuse_child_raw_events(self):
        self.receipt["lifecycle_probes"][0]["raw_event_ids"] = self.receipt["children"][0]["raw_event_ids"][:1]
        self.assertIn("raw event IDs must be unique across all child and lifecycle records",
                      validate_receipt(self.receipt, self.root))

    def test_lifecycle_records_cannot_share_raw_events(self):
        self.receipt["lifecycle_probes"][1]["raw_event_ids"] = self.receipt["lifecycle_probes"][0]["raw_event_ids"][:]
        self.assertIn("raw event IDs must be unique across all child and lifecycle records",
                      validate_receipt(self.receipt, self.root))

    def run_receipt_cli(self, mode, explicit=False):
        command = [sys.executable, str(Path(__file__).with_name("check_live_receipts.py")),
                   mode, "--root", str(self.root)]
        if explicit:
            command.extend(["--receipt", "evidence/test.json"])
        return subprocess.run(command, capture_output=True, text=True)

    def write_matrix(self):
        from tests.check_release_matrix import FIELDS, TARGETS
        rows = ["| Host | Target model | Status | Host version | Model ID | Probe date | Model control | Effort control | Receipt |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for host, model in TARGETS.items():
            row = self.row if host == "Codex" else dict(zip(FIELDS, [host, model, "candidate"] + ["unverified"] * 5 + ["none"]))
            rows.append("| " + " | ".join(row[field] for field in FIELDS) + " |")
        (self.root / "SUPPORT.md").write_text("\n".join(rows) + "\n")

    def test_default_cli_checks_linked_row_context(self):
        today = datetime.now(timezone.utc).date()
        for defect in ("fresh", "stale", "version", "model"):
            with self.subTest(defect=defect):
                probe = (today - timedelta(days=91 if defect == "stale" else 0)).isoformat()
                self.receipt = synthetic_receipt(self.root, probe)
                self.row.update(probe_date=probe, host_version="fixture-2" if defect == "version" else "fixture-1",
                                model_id="other-model" if defect == "model" else "gpt-6-sol")
                self.save()
                self.write_matrix()
                for mode in ("overlap", "model-identity"):
                    result = self.run_receipt_cli(mode)
                    self.assertEqual(result.returncode, 0 if defect == "fresh" else 1, result.stdout + result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    # Explicit fixture mode checks structure without matrix promotion.
                    self.assertEqual(self.run_receipt_cli(mode, explicit=True).returncode, 0)

    def test_dot_receipt_path_returns_failure(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("check_live_receipts.py")),
                                 "overlap", "--root", str(self.root), "--receipt", "."],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_extreme_timezone_returns_failure(self):
        self.receipt["children"][0]["start"] = "0001-01-01T00:00:00+23:59"
        self.save()
        result = self.run_receipt_cli("overlap", explicit=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_values_fail_without_crashing(self):
        mutations = [
            lambda r: r["children"][0].pop("child_id"),
            lambda r: r["lifecycle_probes"][0].update(terminal_state=[]),
        ]
        for mutate in mutations:
            receipt = copy.deepcopy(self.receipt)
            mutate(receipt)
            self.assertTrue(validate_receipt(receipt, self.root))

    def test_receipt_accepts_unknown_termination_and_unexposed_effort(self):
        self.receipt["effort_exposed"] = False
        for child in self.receipt["children"]:
            child["requested_effort"] = None
            child["reported_effort"] = None
        self.assertEqual(validate_receipt(self.receipt, self.root), [])


if __name__ == "__main__":
    unittest.main()
