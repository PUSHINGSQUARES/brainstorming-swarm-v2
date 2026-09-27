"""Negative probes for the digest acceptance boundary."""

import contextlib
import io
import json
import unittest

from scripts.check_campaign import LIMITS, main, validate_campaign, validate_leg, validate_evidence
from tests.test_checker import CampaignCase


class DigestSchemaTests(CampaignCase):
    def setUp(self):
        super().setUp()
        self.campaign_data = self.campaign()
        self.gather = json.loads((self.root / "digests/g1.json").read_text())

    def save(self, leg_id, digest):
        (self.root / "digests" / f"{leg_id}.json").write_text(json.dumps(digest))

    def role(self, leg_id, kind, status="accepted"):
        row = dict(self.campaign_data["roles"][0])
        row.update(leg_id=leg_id, role=kind, artifact=f"digests/{leg_id}.json", status=status)
        self.campaign_data["roles"].append(row)
        self.save_campaign(self.campaign_data)
        return row

    def draft(self, status="accepted"):
        self.role("d1", "draft", status)
        self.campaign_data["approaches"] = [{"approach_id": "a1", "author_leg_id": "d1"}]
        self.save_campaign(self.campaign_data)
        digest = dict(self.gather)
        digest.update(leg_id="d1", role="draft", artifact="digests/d1.json",
                      revision=1, supersedes=None, approach_id="a1", author_leg_id="d1",
                      title="Signs", central_assumption="Visitors can read the sign.",
                      proposal="Add a compact sign.", evidence=[], dependencies=[], risks=[],
                      rough_effort="One test.", falsifying_test="Visitors cannot read it.")
        digest.pop("findings")
        digest.pop("inferences")
        digest.pop("gaps")
        digest.pop("lens", None)
        self.save("d1", digest)
        return digest

    def judge(self, draft=None):
        draft = draft or self.draft()
        self.role("j1", "judge")
        digest = dict(self.gather)
        digest.update(leg_id="j1", role="judge", artifact="digests/j1.json",
                      revision=1, supersedes=None, target_id="a1", target_artifact="digests/d1.json",
                      target_revision=1, judge_leg_id="j1", verdict="keep", severity="none",
                      reason="Review complete.", counterevidence=[], consequence="No known issue.",
                      keep_clauses=[], unknowns=[], required_revision="")
        for key in ("findings", "inferences", "gaps", "lens"):
            digest.pop(key, None)
        self.save("j1", digest)
        return digest

    def assert_both_reject(self, leg_id, fragment):
        self.assertIn(fragment, " ".join(validate_campaign(self.root)))
        self.assertIn(fragment, " ".join(validate_leg(self.root, leg_id)))

    def test_legacy_mixed_gather_finding_is_rejected(self):
        self.gather["findings"][0].pop("finding_id")
        self.gather["findings"][0].pop("source_fact")
        self.gather["findings"][0]["claim"] = (
            "Two of six volunteers read the sign; this contradicts the supplier's universal claim."
        )
        self.gather["findings"][0]["basis"] = "observation"
        self.gather.pop("inferences")
        self.save("g1", self.gather)
        self.assert_both_reject("g1", "source_fact is required")
        self.assert_both_reject("g1", "legacy claim is forbidden")

    def test_legacy_mixed_judge_counterevidence_is_rejected(self):
        judge = self.judge()
        judge["counterevidence"] = [{
            "claim": "The entrance has one narrow wall; the draft requires a site survey.",
            "evidence": {"kind": "file", "path": "sources/brief.md", "lines": [1, 1]},
        }]
        self.save("j1", judge)
        self.assert_both_reject("j1", "source_fact is required")
        self.assert_both_reject("j1", "legacy claim is forbidden")

    def test_gather_inference_links_require_distinct_anchored_findings(self):
        second = json.loads(json.dumps(self.gather["findings"][0]))
        second["finding_id"] = "f2"
        second["source_fact"] = "The brief also identifies two corridor junctions."
        self.gather["findings"].append(second)
        self.gather["inferences"] = [{"claim": "Both facts constrain placement.",
                                       "premise_ids": ["f1", "f2"]}]
        self.save("g1", self.gather)
        self.assertEqual(validate_leg(self.root, "g1"), [])
        mutations = (
            ("duplicate finding_id", lambda d: d["findings"][1].update(finding_id="f1")),
            ("duplicate premise_id", lambda d: d["inferences"][0].update(premise_ids=["f1", "f1"])),
            ("unresolved premise_id", lambda d: d["inferences"][0].update(premise_ids=["f1", "missing"])),
            ("nonempty list", lambda d: d["inferences"][0].update(premise_ids=[])),
            ("nonblank finding IDs", lambda d: d["inferences"][0].update(premise_ids=["f1", " "])),
            ("claim is required", lambda d: d["inferences"][0].update(claim=" ")),
            ("direct evidence is forbidden", lambda d: d["inferences"][0].update(evidence={"kind": "supplied", "id": "dummy"})),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                changed = json.loads(json.dumps(self.gather))
                mutate(changed)
                self.save("g1", changed)
                self.assert_both_reject("g1", expected)

    def test_gather_rejects_missing_and_malformed_new_fields(self):
        for key, value, expected in (
            ("inferences", None, "inferences must be a list"),
            ("inferences", [{}], "claim is required"),
            ("findings", ["not an object"], "must be an object"),
        ):
            with self.subTest(key=key, value=value):
                changed = json.loads(json.dumps(self.gather))
                changed[key] = value
                self.save("g1", changed)
                self.assert_both_reject("g1", expected)
        for legacy in ("claim", "basis"):
            changed = json.loads(json.dumps(self.gather))
            changed["findings"][0][legacy] = "old"
            self.save("g1", changed)
            self.assert_both_reject("g1", "legacy %s is forbidden" % legacy)

    def test_judge_split_item_requires_bearing_in_both_modes(self):
        judge = self.judge()
        judge["counterevidence"] = [{"source_fact": "The brief describes one narrow wall.",
                                      "bearing_on_target": "Placement needs measurement.",
                                      "evidence": {"kind": "file", "path": "sources/brief.md", "lines": [1, 1]}}]
        self.save("j1", judge)
        self.assertEqual(validate_leg(self.root, "j1"), [])
        for value in ("", " ", None, []):
            with self.subTest(value=value):
                judge["counterevidence"][0]["bearing_on_target"] = value
                self.save("j1", judge)
                self.assert_both_reject("j1", "bearing_on_target is required")

    def test_gather_required_fields_and_allowed_empty(self):
        self.gather.update(revision=1, supersedes=None, lens="Visitor access")
        self.save("g1", self.gather)
        self.assertEqual(validate_leg(self.root, "g1"), [])
        for key, value, expected in (
            ("lens", "", "lens"), ("gaps", [""], "gaps"),
            ("revision", True, "revision"), ("supersedes", "", "supersedes"),
        ):
            with self.subTest(key=key):
                original = self.gather[key]
                self.gather[key] = value
                self.save("g1", self.gather)
                self.assert_both_reject("g1", expected)
                self.gather[key] = original
        for key, value in (("finding_id", ""), ("source_fact", "")):
            with self.subTest(key=key):
                original = self.gather["findings"][0][key]
                self.gather["findings"][0][key] = value
                self.save("g1", self.gather)
                self.assert_both_reject("g1", key)
                self.gather["findings"][0][key] = original
        self.gather["findings"] = []
        self.gather["inferences"] = []
        self.gather["gaps"] = []
        self.save("g1", self.gather)
        self.assertEqual(validate_leg(self.root, "g1"), [])

    def test_draft_required_fields_and_reverse_link(self):
        digest = self.draft()
        self.assertEqual(validate_leg(self.root, "d1"), [])
        for key, value in (("title", ""), ("proposal", ""), ("falsifying_test", ""),
                           ("dependencies", [""]), ("risks", "none")):
            with self.subTest(key=key):
                original = digest[key]
                digest[key] = value
                self.save("d1", digest)
                self.assert_both_reject("d1", key)
                digest[key] = original
        self.save("d1", digest)
        self.campaign_data["approaches"].append({"approach_id": "a2", "author_leg_id": "d1"})
        self.save_campaign(self.campaign_data)
        self.assertIn("approach a2 does not match author draft", " ".join(validate_campaign(self.root)))

    def test_judge_requires_current_accepted_draft_and_shape(self):
        draft = self.draft()
        judge = self.judge(draft)
        self.assertEqual(validate_leg(self.root, "j1"), [])
        for key, value in (("target_artifact", "digests/missing.json"),
                           ("target_revision", 999), ("severity", "low"),
                           ("consequence", ""), ("keep_clauses", [""]),
                           ("unknowns", "bad"), ("required_revision", None)):
            with self.subTest(key=key):
                original = judge[key]
                judge[key] = value
                self.save("j1", judge)
                self.assert_both_reject("j1", key)
                judge[key] = original
        judge["verdict"] = "revise"
        self.save("j1", judge)
        self.assert_both_reject("j1", "required_revision")
        judge["verdict"] = "keep"
        self.save("j1", judge)
        self.campaign_data["roles"][2]["status"] = "incomplete"
        self.save_campaign(self.campaign_data)
        self.assert_both_reject("j1", "accepted")

    def test_judge_rejects_non_draft_author_and_duplicate_author_id(self):
        self.judge()
        self.campaign_data["approaches"][0]["author_leg_id"] = "g1"
        self.save_campaign(self.campaign_data)
        self.assert_both_reject("j1", "draft")
        self.campaign_data["approaches"][0]["author_leg_id"] = "d1"
        self.campaign_data["roles"].append(dict(self.campaign_data["roles"][2]))
        self.save_campaign(self.campaign_data)
        self.assertIn("duplicate leg_id", " ".join(validate_leg(self.root, "j1")))

    def test_judge_author_self_link_returns_error_without_recursing(self):
        self.judge()
        self.campaign_data["approaches"][0]["author_leg_id"] = "j1"
        self.save_campaign(self.campaign_data)
        self.assertIn("author cannot judge own approach", " ".join(validate_leg(self.root, "j1")))

    def test_judge_leg_checks_linked_author_metadata(self):
        self.judge()
        self.campaign_data["roles"][2]["host"] = ""
        self.save_campaign(self.campaign_data)
        self.assertIn("roles[0].host is required", " ".join(validate_leg(self.root, "j1")))

    def test_revision_predecessor_allows_malformed_original_but_checks_lineage(self):
        self.gather.update(revision=2, supersedes="digests/g1.r1.json", lens="Access")
        predecessor = self.root / "digests/g1.r1.json"
        predecessor.write_text('{"leg_id":"g1","role":"gather","revision":1}')
        self.save("g1", self.gather)
        self.assertEqual(validate_leg(self.root, "g1"), [])
        predecessor.write_text('{"leg_id":"other","role":"gather","revision":1}')
        self.assert_both_reject("g1", "supersedes")
        predecessor.write_text('{"leg_id":"g1","role":"gather","revision":2}')
        self.assert_both_reject("g1", "supersedes")
        self.gather["supersedes"] = "digests/g1.json"
        self.save("g1", self.gather)
        self.assert_both_reject("g1", "supersedes")

    def test_file_line_bounds_and_url_syntax(self):
        self.gather["findings"][0]["evidence"]["lines"] = [1, 999]
        self.save("g1", self.gather)
        self.assert_both_reject("g1", "line")
        self.assertIn("url", " ".join(validate_evidence(
            {"kind": "url", "url": "not a URL", "section": "A"})))
        self.assertIn("url", " ".join(validate_evidence(
            {"kind": "url", "url": "https://[broken", "section": "A"})))

    def test_stale_accepted_judge_does_not_cover_approach(self):
        self.judge()
        judge = json.loads((self.root / "digests/j1.json").read_text())
        judge["target_revision"] = 2
        self.save("j1", judge)
        errors = " ".join(validate_campaign(self.root))
        self.assertIn("target_revision", errors)
        self.assertIn("approach a1 incomplete", errors)

    def test_solo_campaign_rejects_pending_judge_in_both_modes(self):
        self.judge()
        self.campaign_data["status"] = "solo_analysis"
        self.campaign_data["roles"][3]["status"] = "incomplete"
        self.save_campaign(self.campaign_data)
        self.assertIn("solo_analysis", " ".join(validate_leg(self.root, "j1")))
        self.assertIn("solo_analysis", " ".join(validate_campaign(self.root)))
        self.assertEqual(validate_leg(self.root, "g1"), [])

    def test_malformed_judge_enums_return_errors_in_both_modes(self):
        judge = self.judge()
        for key in ("severity", "verdict"):
            for invalid in ([], {}):
                with self.subTest(key=key, invalid=invalid):
                    original = judge[key]
                    judge[key] = invalid
                    self.save("j1", judge)
                    self.assert_both_reject("j1", key)
                    for args in ([str(self.root)], [str(self.root), "--leg", "j1"]):
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            self.assertEqual(main(args), 1)
                        self.assertIn("ERROR:", output.getvalue())
                        self.assertIn(LIMITS, output.getvalue())
                    judge[key] = original


if __name__ == "__main__":
    unittest.main()
