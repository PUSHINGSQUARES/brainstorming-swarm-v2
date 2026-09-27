import contextlib
import io
import json
import unittest

from scripts.check_campaign import main, validate_campaign
from tests.test_checker import CampaignCase


class LegCheckTests(CampaignCase):
    def check_leg(self, leg_id="g1"):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                result = main([str(self.root), "--leg", leg_id])
            except SystemExit as exc:
                result = exc.code
        return result, output.getvalue()

    def digest(self, leg_id="g1"):
        path = self.root / "digests" / (leg_id + ".json")
        return json.loads(path.read_text())

    def save_digest(self, digest, leg_id="g1"):
        (self.root / "digests" / (leg_id + ".json")).write_text(json.dumps(digest))

    def draft_digest(self):
        digest = self.digest()
        digest.update(leg_id="d1", role="draft", artifact="digests/d1.json",
                      revision=1, supersedes=None, approach_id="a1", author_leg_id="d1",
                      title="Signs", central_assumption="Visitors can read the sign.",
                      proposal="Add a compact sign.", evidence=[], dependencies=[], risks=[],
                      rough_effort="One test.", falsifying_test="Visitors cannot read it.")
        for key in ("findings", "gaps", "lens"):
            digest.pop(key, None)
        return digest

    def add_role(self, leg_id, role, status="accepted"):
        campaign = self.campaign()
        row = dict(campaign["roles"][0])
        row.update(leg_id=leg_id, role=role, artifact="digests/%s.json" % leg_id, status=status)
        campaign["roles"].append(row)
        self.save_campaign(campaign)

    def test_valid_gather_passes_while_future_role_artifact_is_missing(self):
        self.add_role("d1", "draft", status="incomplete")
        self.assertIn("missing artifact", " ".join(validate_campaign(self.root)))
        code, output = self.check_leg()
        self.assertEqual(code, 0, output)
        self.assertIn("g1", output)
        self.assertIn("structure only", output.lower())

    def test_selected_gather_ignores_malformed_future_gather_rows(self):
        campaign = self.campaign()
        campaign["roles"].append({"leg_id": "g3", "role": "gather", "status": [],
                                  "artifact": "digests/g3.json"})
        self.save_campaign(campaign)
        self.assertEqual(self.check_leg()[0], 0)

        campaign["roles"][-1] = {"leg_id": [], "role": "gather", "status": "accepted",
                                 "artifact": "digests/g1.json"}
        self.save_campaign(campaign)
        self.assertEqual(self.check_leg()[0], 0)

    def test_selected_gather_ignores_future_role_pointing_to_other_digest(self):
        campaign = self.campaign()
        campaign["roles"].append({"leg_id": "g3", "role": "gather", "status": "incomplete",
                                  "artifact": "digests/g1.json"})
        self.save_campaign(campaign)
        code, output = self.check_leg()
        self.assertEqual(code, 0, output)

    def test_incomplete_row_can_validate_corrected_r2_before_acceptance(self):
        campaign = self.campaign()
        campaign["roles"][0]["status"] = "incomplete"
        self.save_campaign(campaign)
        first = self.digest()
        first["findings"][0]["evidence"]["lines"] = [1]
        self.save_digest(first)
        code, output = self.check_leg()
        self.assertEqual(code, 1)
        self.assertIn("positive [start, end] range", output)
        corrected = self.digest("g2")
        corrected.update(leg_id="g1", artifact="digests/g1.r2.json", revision=2,
                         supersedes="digests/g1.json", lens=first["lens"])
        (self.root / "digests" / "g1.r2.json").write_text(json.dumps(corrected))
        campaign["roles"][0]["artifact"] = "digests/g1.r2.json"
        self.save_campaign(campaign)
        code, output = self.check_leg()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.campaign()["roles"][0]["status"], "incomplete")

    def test_unknown_leg_fails_with_structure_only_limit(self):
        code, output = self.check_leg("missing")
        self.assertEqual(code, 1)
        self.assertIn("unknown leg", output.lower())
        self.assertIn("structure only", output.lower())

    def test_selected_digest_malformed_json_fails(self):
        (self.root / "digests" / "g1.json").write_text("{")
        code, output = self.check_leg()
        self.assertEqual(code, 1)
        self.assertIn("invalid JSON", output)

    def test_one_number_file_line_range_fails_before_acceptance(self):
        digest = self.digest()
        digest["findings"][0]["evidence"]["lines"] = [3]
        self.save_digest(digest)
        code, output = self.check_leg()
        self.assertEqual(code, 1)
        self.assertIn("positive [start, end] range", output)

    def test_selected_local_evidence_must_exist(self):
        digest = self.digest()
        digest["findings"][0]["evidence"]["path"] = "sources/missing.md"
        self.save_digest(digest)
        code, output = self.check_leg()
        self.assertEqual(code, 1)
        self.assertIn("missing evidence file", output)

    def test_selected_digest_metadata_must_match_role(self):
        digest = self.digest()
        digest["model"] = "another-model"
        self.save_digest(digest)
        code, output = self.check_leg()
        self.assertEqual(code, 1)
        self.assertIn("model does not match role", output)

    def test_draft_links_to_its_own_approach(self):
        self.add_role("d1", "draft")
        campaign = self.campaign()
        campaign["approaches"] = [{"approach_id": "a1", "author_leg_id": "d1"}]
        self.save_campaign(campaign)
        digest = self.draft_digest()
        self.save_digest(digest, "d1")
        code, output = self.check_leg("d1")
        self.assertEqual(code, 0, output)
        campaign["approaches"][0]["author_leg_id"] = "g1"
        self.save_campaign(campaign)
        code, output = self.check_leg("d1")
        self.assertEqual(code, 1)
        self.assertIn("does not match approach author", output)

    def test_draft_digest_author_must_match_role_and_approach(self):
        self.add_role("d1", "draft")
        campaign = self.campaign()
        campaign["approaches"] = [{"approach_id": "a1", "author_leg_id": "d1"}]
        self.save_campaign(campaign)
        digest = self.draft_digest()
        digest.pop("author_leg_id")
        self.save_digest(digest, "d1")
        code, output = self.check_leg("d1")
        self.assertEqual(code, 1, output)
        self.assertIn("author_leg_id", output)
        self.assertIn("draft d1 author_leg_id does not match role", validate_campaign(self.root))
        digest["author_leg_id"] = "g1"
        self.save_digest(digest, "d1")
        code, output = self.check_leg("d1")
        self.assertEqual(code, 1, output)
        self.assertIn("author_leg_id", output)
        digest["author_leg_id"] = "d1"
        self.save_digest(digest, "d1")
        code, output = self.check_leg("d1")
        self.assertEqual(code, 0, output)

    def test_judge_checks_target_and_independence_with_accepted_draft(self):
        self.add_role("d1", "draft", status="accepted")
        self.add_role("j1", "judge")
        campaign = self.campaign()
        campaign["approaches"] = [{"approach_id": "a1", "author_leg_id": "d1"}]
        self.save_campaign(campaign)
        self.save_digest(self.draft_digest(), "d1")
        digest = self.digest()
        digest.update(leg_id="j1", role="judge", artifact="digests/j1.json",
                      target_id="a1", target_artifact="digests/d1.json", target_revision=1,
                      judge_leg_id="j1", reason="Check the draft.", verdict="keep",
                      severity="none", consequence="No known issue.", keep_clauses=[],
                      unknowns=[], required_revision="", counterevidence=[])
        for key in ("findings", "gaps", "lens"):
            digest.pop(key, None)
        self.save_digest(digest, "j1")
        code, output = self.check_leg("j1")
        self.assertEqual(code, 0, output)
        digest["target_id"] = "missing"
        self.save_digest(digest, "j1")
        code, output = self.check_leg("j1")
        self.assertEqual(code, 1)
        self.assertIn("target_id has no approach", output)
        digest["target_id"] = "a1"
        self.save_digest(digest, "j1")
        campaign["approaches"][0]["author_leg_id"] = "j1"
        self.save_campaign(campaign)
        code, output = self.check_leg("j1")
        self.assertEqual(code, 1)
        self.assertIn("author cannot judge own approach", output)


if __name__ == "__main__":
    unittest.main()
