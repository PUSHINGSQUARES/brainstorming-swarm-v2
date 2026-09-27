"""Red-check the public gates in disposable Git repositories."""

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TESTS = Path(__file__).resolve().parent
TOKEN_CHECK = TESTS / "check_public_tokens.py"
SURFACE_CHECK = TESTS / "check_public_surface.py"


def file_id(name):
    return "file#" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]


class PublicSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "tester@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Test Operator"], check=True)
        (self.root / "README.md").write_text("A clean public file.\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-qm", "base")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def run_gate(self, script, *args):
        return subprocess.run([sys.executable, str(script), "--root", str(self.root), *args],
                              capture_output=True, text=True)

    def test_private_literal_catches_tracked_and_untracked_without_echo(self):
        fake = "invented" + "PrivateMarker"
        patterns = self.root.parent / (self.root.name + "-patterns.txt")
        patterns.write_text(fake + "\n", encoding="utf-8")
        self.addCleanup(patterns.unlink)
        self.assertEqual(self.run_gate(TOKEN_CHECK, "--patterns", str(patterns)).returncode, 0)
        (self.root / "README.md").write_text(fake + "\n", encoding="utf-8")
        (self.root / "extra.md").write_text(fake + "\n", encoding="utf-8")
        result = self.run_gate(TOKEN_CHECK, "--patterns", str(patterns))
        self.assertEqual(result.returncode, 1)
        self.assertIn(file_id("README.md") + ":1", result.stdout)
        self.assertIn(file_id("extra.md") + ":1", result.stdout)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_operator_path_mutation_is_red_without_echo(self):
        fake = "/Vol" + "umes/InventedOperator/work/secret.txt"
        self.assertEqual(self.run_gate(SURFACE_CHECK, "paths").returncode, 0)
        (self.root / "extra.md").write_text("See " + fake + "\n", encoding="utf-8")
        result = self.run_gate(SURFACE_CHECK, "paths")
        self.assertEqual(result.returncode, 1)
        self.assertIn(file_id("extra.md") + ":1", result.stdout)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_credential_current_and_history_mutations_are_red(self):
        fake = "AK" + "IA" + "A" * 16
        self.assertEqual(self.run_gate(SURFACE_CHECK, "credentials", "--history").returncode, 0)
        (self.root / "secret.md").write_text(fake + "\n", encoding="utf-8")
        current = self.run_gate(SURFACE_CHECK, "credentials")
        self.assertEqual(current.returncode, 1)
        self.assertNotIn(fake, current.stdout + current.stderr)
        self.git("add", "secret.md")
        self.git("commit", "-qm", "fake historical value")
        (self.root / "secret.md").write_text("Cleared from current tree.\n", encoding="utf-8")
        self.git("add", "secret.md")
        self.git("commit", "-qm", "remove fake value")
        self.assertEqual(self.run_gate(SURFACE_CHECK, "credentials").returncode, 0)
        history = self.run_gate(SURFACE_CHECK, "credentials", "--history")
        self.assertEqual(history.returncode, 1)
        self.assertIn("HISTORY CREDENTIAL:", history.stdout)
        self.assertNotIn(fake, history.stdout + history.stderr)

    def test_credential_in_commit_message_is_red(self):
        fake = "AK" + "IA" + "B" * 16
        (self.root / "README.md").write_text("Second clean file.\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-qm", fake)
        result = self.run_gate(SURFACE_CHECK, "credentials", "--history")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_untracked_dotenv_credential_is_red(self):
        fake = "AK" + "IA" + "C" * 16
        (self.root / ".env").write_text(fake + "\n", encoding="utf-8")
        result = self.run_gate(SURFACE_CHECK, "credentials")
        self.assertEqual(result.returncode, 1)
        self.assertIn(file_id(".env") + ":1", result.stdout)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_untracked_javascript_private_literal_is_red(self):
        fake = "invented" + "PrivateMarker"
        patterns = self.root.parent / (self.root.name + "-patterns.txt")
        patterns.write_text(fake + "\n", encoding="utf-8")
        self.addCleanup(patterns.unlink)
        (self.root / "client.js").write_text(fake + "\n", encoding="utf-8")
        result = self.run_gate(TOKEN_CHECK, "--patterns", str(patterns))
        self.assertEqual(result.returncode, 1)
        self.assertIn(file_id("client.js") + ":1", result.stdout)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_binary_candidate_requires_review(self):
        (self.root / "payload.bin").write_bytes(b"opaque\x00data")
        result = self.run_gate(SURFACE_CHECK, "credentials")
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires review", result.stdout)

    def test_quoted_json_key_is_red_in_current_and_history(self):
        fake = "invented" + "CredentialValue123"
        (self.root / "config.json").write_text('{"api_key": "' + fake + '"}\n', encoding="utf-8")
        current = self.run_gate(SURFACE_CHECK, "credentials")
        self.assertEqual(current.returncode, 1)
        self.git("add", "config.json")
        self.git("commit", "-qm", "fake config")
        (self.root / "config.json").write_text("{}\n", encoding="utf-8")
        self.git("add", "config.json")
        self.git("commit", "-qm", "clear config")
        history = self.run_gate(SURFACE_CHECK, "credentials", "--history")
        self.assertEqual(history.returncode, 1)
        self.assertNotIn(fake, current.stdout + history.stdout)

    def test_windows_operator_path_is_red(self):
        fake = "C:" + "\\Users\\InventedOperator\\work\\file.txt"
        (self.root / "notes.md").write_text(fake + "\n", encoding="utf-8")
        result = self.run_gate(SURFACE_CHECK, "paths")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(fake, result.stdout)

    def test_ignored_private_key_file_is_red(self):
        (self.root / ".gitignore").write_text("*.pem\n", encoding="utf-8")
        fake = "-----BEGIN " + "PRIVATE KEY-----"
        (self.root / "key.pem").write_text(fake + "\n", encoding="utf-8")
        result = self.run_gate(SURFACE_CHECK, "credentials")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(fake, result.stdout)

    def test_private_marker_in_filename_is_red_without_echo(self):
        fake = "invented" + "PrivateMarker"
        patterns = self.root.parent / (self.root.name + "-patterns.txt")
        patterns.write_text(fake + "\n", encoding="utf-8")
        self.addCleanup(patterns.unlink)
        (self.root / (fake + ".md")).write_text("Clean content.\n", encoding="utf-8")
        result = self.run_gate(TOKEN_CHECK, "--patterns", str(patterns))
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_utf16_historical_credential_is_red(self):
        fake = "AK" + "IA" + "D" * 16
        (self.root / "old.txt").write_bytes(fake.encode("utf-16"))
        self.git("add", "old.txt")
        self.git("commit", "-qm", "fake encoded value")
        (self.root / "old.txt").write_text("Cleared.\n", encoding="utf-8")
        self.git("add", "old.txt")
        self.git("commit", "-qm", "clear encoded value")
        result = self.run_gate(SURFACE_CHECK, "credentials", "--history")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_undecodable_historical_blob_requires_review(self):
        (self.root / "old.bin").write_bytes(b"opaque\x00data")
        self.git("add", "old.bin")
        self.git("commit", "-qm", "fake binary history")
        (self.root / "old.bin").write_text("Cleared.\n", encoding="utf-8")
        self.git("add", "old.bin")
        self.git("commit", "-qm", "clear binary history")
        result = self.run_gate(SURFACE_CHECK, "credentials", "--history")
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires review", result.stdout)

    def test_sensitive_filename_is_hidden_when_content_matches(self):
        marker = "invented" + "PrivateMarker"
        fake = "AK" + "IA" + "E" * 16
        (self.root / (marker + ".md")).write_text(fake + "\n", encoding="utf-8")
        result = self.run_gate(SURFACE_CHECK, "credentials")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(marker, result.stdout + result.stderr)
        self.assertNotIn(fake, result.stdout + result.stderr)

    def test_pass_message_names_only_checked_mode(self):
        path_result = self.run_gate(SURFACE_CHECK, "paths")
        self.assertEqual(path_result.returncode, 0)
        self.assertNotIn("credential", path_result.stdout.lower())
        credential_result = self.run_gate(SURFACE_CHECK, "credentials")
        self.assertEqual(credential_result.returncode, 0)
        self.assertNotIn("operator path", credential_result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
