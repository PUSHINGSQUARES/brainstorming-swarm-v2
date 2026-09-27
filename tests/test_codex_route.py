"""Synthetic Codex session records for the local route preflight."""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.check_codex_route import main


# Fixed synthetic UUIDs. Never use IDs copied from a live session in public fixtures.
THREAD_ID = "00000000-0000-4000-8000-000000000001"
OTHER_ID = "00000000-0000-4000-8000-000000000002"


def record(kind, payload):
    return {"type": kind, "payload": payload}


class CodexRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_rollout(self, records, name=None):
        path = self.root / "2026" / "09" / "27" / (
            name or "rollout-2026-09-27T00-00-00-%s.jsonl" % THREAD_ID
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
        return path

    def valid_records(self):
        return [
            record("session_meta", {"id": THREAD_ID, "account_id": "do-not-print"}),
            record("event_msg", {"message": "private prompt do-not-print"}),
            record("turn_context", {"model": "gpt-6-sol", "effort": "medium"}),
        ]

    def check(self, thread_id=THREAD_ID, model="gpt-6-sol", effort="medium"):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([thread_id, model, effort, "--session-root", str(self.root)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_accepts_one_exact_matching_rollout_without_leaking_contents(self):
        self.write_rollout(self.valid_records())
        self.write_rollout(["not JSON objects"], name="rollout-%s.jsonl" % OTHER_ID)
        code, output, errors = self.check()
        self.assertEqual(code, 0, errors)
        self.assertIn("gpt-6-sol", output)
        self.assertIn("medium", output)
        self.assertIn(THREAD_ID, output)
        self.assertNotIn("do-not-print", output + errors)

    def test_rejects_missing_or_duplicate_exact_filename(self):
        self.assertNotEqual(self.check()[0], 0)
        self.write_rollout(self.valid_records())
        self.write_rollout(self.valid_records(), name="another-%s.jsonl" % THREAD_ID)
        self.assertNotEqual(self.check()[0], 0)

    def test_filename_requires_uuid_boundary(self):
        self.write_rollout(self.valid_records(), name="rollout-prefix%s.jsonl" % THREAD_ID)
        self.assertNotEqual(self.check()[0], 0)

    def test_rejects_session_meta_mismatch_or_duplicate(self):
        records = self.valid_records()
        records[0] = record("session_meta", {"id": OTHER_ID})
        self.write_rollout(records)
        self.assertNotEqual(self.check()[0], 0)
        self.write_rollout(self.valid_records() + [self.valid_records()[0]])
        self.assertNotEqual(self.check()[0], 0)

    def test_accepts_consistent_multi_turn_context(self):
        records = self.valid_records()
        self.write_rollout(records + [records[-1]])
        self.assertEqual(self.check()[0], 0)

    def test_rejects_missing_or_mismatched_turn_context(self):
        records = self.valid_records()
        self.write_rollout(records[:2])
        self.assertNotEqual(self.check()[0], 0)
        self.write_rollout(records + [record("turn_context", {"model": "gpt-6-astra", "effort": "medium"})])
        self.assertNotEqual(self.check()[0], 0)
        self.write_rollout(records[:2] + [record("turn_context", {"model": "gpt-6-astra", "effort": "medium"})])
        self.assertNotEqual(self.check()[0], 0)
        self.write_rollout(records[:2] + [record("turn_context", {"model": "gpt-6-sol", "effort": "high"})])
        self.assertNotEqual(self.check()[0], 0)

    def test_rejects_malformed_and_unreadable_records_without_echo(self):
        path = self.write_rollout(self.valid_records())
        path.write_text('{"type":"session_meta","payload":{"id":"%s"}}\n{bad secret text\n' % THREAD_ID)
        code, output, errors = self.check()
        self.assertNotEqual(code, 0)
        self.assertNotIn("secret text", output + errors)
        path.write_bytes(b"\xff\xfe")
        self.assertNotEqual(self.check()[0], 0)

    def test_rejects_noncanonical_thread_id_before_search(self):
        self.write_rollout(self.valid_records())
        self.assertNotEqual(self.check("../" + THREAD_ID)[0], 0)

    def _replacement_at_open(self, target_name, selected_name, replace):
        """Swap a synthetic path at either old Path.open or new descriptor open."""
        real_path_open = Path.open
        real_os_open = os.open
        swapped = False

        def swap_once():
            nonlocal swapped
            if not swapped:
                replace()
                swapped = True

        def path_open(path, *args, **kwargs):
            if str(path).endswith(selected_name):
                swap_once()
            return real_path_open(path, *args, **kwargs)

        def descriptor_open(path, flags, *args, **kwargs):
            if os.fspath(path) == target_name and kwargs.get("dir_fd") is not None:
                swap_once()
            return real_os_open(path, flags, *args, **kwargs)

        supported = set(os.supports_dir_fd)
        supported.add(descriptor_open)
        with (mock.patch.object(Path, "open", path_open),
              mock.patch("scripts.check_codex_route.os.open", descriptor_open),
              mock.patch.object(os, "supports_dir_fd", supported)):
            result = self.check()
        self.assertTrue(swapped, "the test did not reach the selected open boundary")
        self.assertNotEqual(result[0], 0)
        self.assertNotIn("outside-secret", result[1] + result[2])

    def test_rejects_file_replaced_by_outside_symlink_at_open(self):
        selected = self.write_rollout(self.valid_records())
        outside = self.root.parent / (self.root.name + "-outside-file.jsonl")
        outside.write_text("\n".join(json.dumps(row) for row in self.valid_records()) + "\n", encoding="utf-8")
        self.addCleanup(outside.unlink)

        def replace():
            selected.rename(selected.with_suffix(".before"))
            selected.symlink_to(outside)

        self._replacement_at_open(selected.name, selected.name, replace)

    def test_rejects_ancestor_replaced_by_outside_symlink_at_open(self):
        selected = self.write_rollout(self.valid_records())
        outside = self.root.parent / (self.root.name + "-outside-tree")
        target = outside / "09" / "27" / selected.name
        target.parent.mkdir(parents=True)
        target.write_text("\n".join(json.dumps(row) for row in self.valid_records()) + "\n", encoding="utf-8")
        self.addCleanup(lambda: __import__("shutil").rmtree(outside))
        year = self.root / "2026"

        def replace():
            year.rename(self.root / "2026.before")
            year.symlink_to(outside, target_is_directory=True)

        self._replacement_at_open("2026", selected.name, replace)

    def test_deep_json_cli_error_is_sanitized(self):
        path = self.write_rollout(self.valid_records())
        deep = "[" * 2000 + "0" + "]" * 2000
        with path.open("a", encoding="utf-8") as stream:
            stream.write('{"type":"event_msg","payload":{"secret":"outside-secret","deep":' + deep + '}}\n')
        script = Path(__file__).resolve().parents[1] / "scripts" / "check_codex_route.py"
        result = subprocess.run(
            [sys.executable, str(script), THREAD_ID, "gpt-6-sol", "medium", "--session-root", str(self.root)],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn("outside-secret", result.stdout + result.stderr)

    def test_missing_descriptor_support_fails_closed(self):
        self.write_rollout(self.valid_records())
        with mock.patch.object(os, "supports_dir_fd", set()):
            code, output, errors = self.check()
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertIn("safe descriptor traversal unavailable", errors)

    def test_missing_nonblocking_open_fails_closed(self):
        self.write_rollout(self.valid_records())
        nonblocking = os.O_NONBLOCK
        del os.O_NONBLOCK
        try:
            code, output, errors = self.check()
        finally:
            os.O_NONBLOCK = nonblocking
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertIn("safe descriptor traversal unavailable", errors)

    def test_fifo_replacement_returns_without_blocking(self):
        selected = self.write_rollout(self.valid_records())
        probe = """
import os
import sys
from pathlib import Path
from scripts import check_codex_route as route
root, selected = Path(sys.argv[1]), Path(sys.argv[2])
real_open = os.open
def swap(path, flags, *args, **kwargs):
    if os.fspath(path) == selected.name and kwargs.get('dir_fd') is not None:
        selected.rename(selected.with_suffix('.before'))
        os.mkfifo(selected)
    return real_open(path, flags, *args, **kwargs)
os.open = swap
os.supports_dir_fd = set(os.supports_dir_fd) | {swap}
raise SystemExit(route.main([sys.argv[3], 'gpt-6-sol', 'medium', '--session-root', str(root)]))
"""
        result = subprocess.run(
            [sys.executable, "-c", probe, str(self.root), str(selected), THREAD_ID],
            cwd=str(Path(__file__).resolve().parents[1]), capture_output=True, text=True,
            timeout=3, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)

    def test_oversize_line_fails_closed(self):
        path = self.write_rollout(self.valid_records())
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record("event_msg", {"blob": "x" * (4 * 1024 * 1024)})) + "\n")
        code, output, errors = self.check()
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertNotIn("Traceback", errors)

    def test_oversize_rollout_fails_closed(self):
        path = self.write_rollout(self.valid_records())
        row = json.dumps(record("event_msg", {"blob": "x" * (1024 * 1024)})) + "\n"
        with path.open("a", encoding="utf-8") as stream:
            for _ in range(33):
                stream.write(row)
        code, output, errors = self.check()
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertNotIn("Traceback", errors)

    def test_excessive_record_count_fails_closed(self):
        path = self.write_rollout(self.valid_records())
        row = json.dumps(record("event_msg", {})) + "\n"
        with path.open("a", encoding="utf-8") as stream:
            stream.write(row * 100_000)
        code, output, errors = self.check()
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertNotIn("Traceback", errors)


if __name__ == "__main__":
    unittest.main()
