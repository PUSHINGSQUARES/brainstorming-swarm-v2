import contextlib
import hashlib
import io
import json

from scripts.check_campaign import main, validate_campaign, validate_leg
from tests.test_checker import CampaignCase


class EventJournalTests(CampaignCase):
    def run_check(self, *flags):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(self.root), *flags])
        return code, output.getvalue()

    def opt_in(self):
        campaign = self.campaign()
        campaign["events"] = "events.ndjson"
        self.save_campaign(campaign)
        self.write_events([])

    def write_events(self, events):
        (self.root / "events.ndjson").write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
        )

    def digest_hash(self, leg_id="g1"):
        return hashlib.sha256((self.root / "digests" / (leg_id + ".json")).read_bytes()).hexdigest()

    def validation(self, seq=1, leg_id="g1", artifact=None, sha256=None, result="pass"):
        return {
            "seq": seq, "at": "2026-09-27T01:%02d:00Z" % seq, "type": "validation",
            "leg_id": leg_id, "artifact": artifact or "digests/%s.json" % leg_id,
            "sha256": self.digest_hash(leg_id) if sha256 is None else sha256,
            "result": result, "checker": "--leg %s exit 0" % leg_id,
            "source_review": "f1: sources/brief.md:3 supports clause; premise checked",
            "status_during_event": "incomplete",
        }

    def acceptance(self, seq=2, leg_id="g1", artifact=None, sha256=None, validation_seq=1):
        return {
            "seq": seq, "at": "2026-09-27T01:%02d:00Z" % seq, "type": "acceptance",
            "leg_id": leg_id, "artifact": artifact or "digests/%s.json" % leg_id,
            "sha256": self.digest_hash(leg_id) if sha256 is None else sha256,
            "validation_seq": validation_seq,
        }

    def correction(self, seq, corrects_seq, effect="annotation"):
        return {
            "seq": seq, "at": "2026-09-27T01:%02d:00Z" % seq, "type": "correction",
            "corrects_seq": corrects_seq, "reason": "Record entered incorrectly.",
            "effect": effect,
        }

    def accepted_pair(self, leg_id, start):
        return [self.validation(start, leg_id), self.acceptance(start + 1, leg_id, validation_seq=start)]

    def test_legacy_campaign_ignores_journal(self):
        self.assertEqual(validate_campaign(self.root), [])
        self.assertEqual(self.run_check("--leg", "g1")[0], 0)

    def test_accepted_roles_need_prior_matching_validation(self):
        self.opt_in()
        self.write_events([self.acceptance(seq=1)])
        code, output = self.run_check("--events")
        self.assertEqual(code, 1, output)
        self.assertIn("validation", output)
        self.assertIn("validation", " ".join(validate_leg(self.root, "g1")))
        self.assertEqual(self.run_check()[0], 1)
        self.assertEqual(self.run_check("--leg", "g1")[0], 1)

    def test_reversed_order_and_later_correction_stay_invalid(self):
        self.opt_in()
        self.write_events([
            self.acceptance(seq=1, validation_seq=2),
            self.validation(seq=2),
            self.correction(3, 1, "annotation"),
        ])
        code, output = self.run_check("--events")
        self.assertEqual(code, 1, output)
        self.assertIn("preceding", output)

    def test_failed_validation_cannot_authorize_acceptance(self):
        self.opt_in()
        self.write_events([self.validation(result="fail"), self.acceptance()])
        self.assertIn("passing validation", self.run_check("--events")[1])

    def test_newer_failed_review_blocks_older_pass_until_fresh_pass(self):
        self.opt_in()
        old_pass = self.validation(1)
        failed = self.validation(2, result="fail")
        g2_pair = self.accepted_pair("g2", 4)
        self.write_events([old_pass, failed, self.acceptance(3, validation_seq=1), *g2_pair])
        for flags in ((), ("--leg", "g1"), ("--events",)):
            code, output = self.run_check(*flags)
            self.assertEqual(code, 1, output)
            self.assertIn("newer validation", output)
        fresh = self.validation(3)
        self.write_events([old_pass, failed, fresh, self.acceptance(4, validation_seq=3),
                           *self.accepted_pair("g2", 5)])
        for flags in ((), ("--leg", "g1"), ("--events",)):
            self.assertEqual(self.run_check(*flags)[0], 0)

    def test_failure_after_acceptance_suspends_it_until_revocation_and_reacceptance(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + [self.validation(3, result="fail")]
        events += self.accepted_pair("g2", 4)
        self.write_events(events)
        for flags in ((), ("--leg", "g1"), ("--events",)):
            code, output = self.run_check(*flags)
            self.assertEqual(code, 1, output)
            self.assertIn("superseded by a newer validation", output)
        events.insert(3, {
            "seq": 4, "at": "2026-09-27T01:04:00Z", "type": "revocation",
            "leg_id": "g1", "acceptance_seq": 2, "reason": "New failed review closes the barrier.",
        })
        events = events[:4] + [self.validation(5), self.acceptance(6, validation_seq=5)]
        events += self.accepted_pair("g2", 7)
        self.write_events(events)
        for flags in ((), ("--leg", "g1"), ("--events",)):
            self.assertEqual(self.run_check(*flags)[0], 0)

    def test_retracted_preacceptance_field_errors_can_recover_append_only(self):
        self.opt_in()
        for field, value in (("checker", ""), ("sha256", "incorrect-hash")):
            bad = self.validation(1)
            bad[field] = value
            events = [bad, self.correction(2, 1, "retract"),
                      *self.accepted_pair("g1", 3), *self.accepted_pair("g2", 5)]
            self.write_events(events)
            for flags in ((), ("--leg", "g1"), ("--events",)):
                code, output = self.run_check(*flags)
                self.assertEqual(code, 0, (field, flags, output))

    def test_retract_cannot_erase_bad_acceptance_history(self):
        self.opt_in()
        bad = self.validation(1)
        bad["checker"] = ""
        events = [bad, self.acceptance(2), self.correction(3, 1, "retract"),
                  *self.accepted_pair("g1", 4), *self.accepted_pair("g2", 6)]
        self.write_events(events)
        self.assertIn("checker", self.run_check("--events")[1])

    def test_retract_cannot_repair_unparseable_or_blank_physical_line(self):
        self.opt_in()
        recovery = [self.correction(2, 1, "retract"),
                    *self.accepted_pair("g1", 3), *self.accepted_pair("g2", 5)]
        for first_line in ("{broken\n", "\n"):
            (self.root / "events.ndjson").write_text(
                first_line + "".join(json.dumps(event) + "\n" for event in recovery),
                encoding="utf-8",
            )
            code, output = self.run_check("--events")
            self.assertEqual(code, 1, output)
            self.assertIn("events line 1", output)

    def test_generic_source_review_does_not_support_pass(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3)
        events[0]["source_review"] = "reviewed"
        self.write_events(events)
        self.assertIn("source_review", self.run_check("--events")[1])

    def test_current_artifact_tamper_is_rejected(self):
        self.opt_in()
        self.write_events(self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3))
        self.assertEqual(self.run_check("--events")[0], 0)
        (self.root / "digests" / "g1.json").write_text("{}")
        self.assertIn("SHA256", self.run_check("--events")[1])

    def test_new_revision_needs_new_acceptance(self):
        self.opt_in()
        self.write_events(self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3))
        campaign = self.campaign()
        campaign["roles"][0]["artifact"] = "digests/g1.r2.json"
        self.save_campaign(campaign)
        (self.root / "digests" / "g1.r2.json").write_text("{}")
        self.assertIn("current artifact", self.run_check("--events")[1])

    def test_incomplete_leg_passes_before_acceptance_and_events_tolerates_future_digest(self):
        self.opt_in()
        campaign = self.campaign()
        campaign["roles"][0]["status"] = "incomplete"
        campaign["roles"][1]["status"] = "incomplete"
        campaign["roles"][1]["artifact"] = "digests/future.json"
        campaign["synthesis"]["accepted_leg_ids"] = []
        self.save_campaign(campaign)
        self.write_events([self.validation()])
        self.assertEqual(self.run_check("--events")[0], 0)
        self.assertEqual(self.run_check("--leg", "g1")[0], 0)
        self.assertEqual(self.run_check()[0], 1)

    def test_incomplete_role_cannot_retain_active_acceptance(self):
        self.opt_in()
        self.write_events(self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3))
        campaign = self.campaign()
        campaign["roles"][0]["status"] = "incomplete"
        self.save_campaign(campaign)
        self.assertIn("incomplete", self.run_check("--events")[1])

    def test_correction_annotation_keeps_valid_acceptance(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3)
        events.append(self.correction(5, 2))
        self.write_events(events)
        self.assertEqual(self.run_check("--events")[0], 0)

    def test_barrier_unproven_cannot_count_as_acceptance(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3)
        events.append(self.correction(5, 2, "barrier_unproven"))
        self.write_events(events)
        self.assertIn("effective acceptance", self.run_check("--events")[1])

    def test_revocation_requires_new_validation_for_recovery(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3)
        events.append({
            "seq": 5, "at": "2026-09-27T01:05:00Z", "type": "revocation",
            "leg_id": "g1", "acceptance_seq": 2, "reason": "Digest superseded.",
        })
        self.write_events(events)
        self.assertIn("effective acceptance", self.run_check("--events")[1])
        events.append(self.acceptance(6, validation_seq=1))
        self.write_events(events)
        self.assertIn("fresh passing validation", self.run_check("--events")[1])
        events[5] = self.validation(6)
        events.append(self.acceptance(7, validation_seq=6))
        self.write_events(events)
        self.assertEqual(self.run_check("--events")[0], 0)

    def test_failed_revision_remains_visible_while_new_revision_is_accepted(self):
        self.opt_in()
        campaign = self.campaign()
        campaign["roles"][0]["artifact"] = "digests/g1.r2.json"
        self.save_campaign(campaign)
        revised = json.loads((self.root / "digests" / "g1.json").read_text())
        revised.update(artifact="digests/g1.r2.json", revision=2, supersedes="digests/g1.json")
        (self.root / "digests" / "g1.r2.json").write_text(json.dumps(revised))
        new_hash = hashlib.sha256((self.root / "digests" / "g1.r2.json").read_bytes()).hexdigest()
        failed = self.validation(1, result="fail")
        current_validation = self.validation(2, artifact="digests/g1.r2.json", sha256=new_hash)
        current_acceptance = self.acceptance(3, artifact="digests/g1.r2.json", sha256=new_hash, validation_seq=2)
        self.write_events([failed, current_validation, current_acceptance] + self.accepted_pair("g2", 4))
        self.assertEqual(self.run_check()[0], 0)
        self.assertEqual(self.run_check("--leg", "g1")[0], 0)

    def test_null_hash_requires_limit_and_reports_it(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3)
        events[0]["sha256"] = None
        events[1]["sha256"] = None
        self.write_events(events)
        self.assertIn("hash_limit", self.run_check("--events")[1])
        events[0]["hash_limit"] = "No local hash tool; artifact tampering cannot be checked."
        events[1]["hash_limit"] = events[0]["hash_limit"]
        self.write_events(events)
        code, output = self.run_check("--events")
        self.assertEqual(code, 0, output)
        self.assertIn("tampering cannot be checked", output)

    def test_null_hash_rejects_false_integrity_claim(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3)
        for event in events[:2]:
            event["sha256"] = None
            event["hash_limit"] = "Tamper-proof and verified."
        self.write_events(events)
        for flags in ((), ("--leg", "g1"), ("--events",)):
            code, output = self.run_check(*flags)
            self.assertEqual(code, 1, output)
            self.assertIn("hash_limit", output)

    def test_malformed_json_sequence_and_unknown_fields_fail_gracefully(self):
        self.opt_in()
        (self.root / "events.ndjson").write_text("{bad\n")
        self.assertIn("invalid JSON", self.run_check("--events")[1])
        event = self.validation(seq=2)
        event["surprise"] = 1
        self.write_events([event])
        output = self.run_check("--events")[1]
        self.assertIn("seq", output)
        self.assertIn("unknown field", output)

    def test_unknown_event_and_path_traversal_fail_gracefully(self):
        self.opt_in()
        event = self.validation()
        event["type"] = "teleport"
        self.write_events([event])
        self.assertIn("unknown event type", self.run_check("--events")[1])
        event = self.validation(artifact="../escape.json")
        self.write_events([event])
        self.assertIn("escapes campaign root", self.run_check("--events")[1])

    def test_malformed_field_types_do_not_crash(self):
        self.opt_in()
        event = self.validation()
        event["type"] = []
        self.write_events([event])
        self.assertIn("unknown event type", self.run_check("--events")[1])
        event = self.validation()
        event["result"] = []
        self.write_events([event])
        self.assertIn("result", self.run_check("--events")[1])
        event = self.acceptance(seq=1)
        event["leg_id"] = []
        self.write_events([event])
        self.assertEqual(self.run_check("--events")[0], 1)
        event = {
            "seq": 1, "at": "2026-09-27T01:01:00Z", "type": "revocation",
            "leg_id": [], "acceptance_seq": 1, "reason": "Mistyped leg.",
        }
        self.write_events([event])
        self.assertEqual(self.run_check("--events")[0], 1)

    def test_backward_timestamp_cannot_reorder_history(self):
        self.opt_in()
        events = self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3)
        events[3]["at"] = "2026-09-27T01:00:00Z"
        self.write_events(events)
        self.assertIn("backdating", self.run_check("--events")[1])

    def test_full_leg_and_events_agree_on_valid_journal(self):
        self.opt_in()
        self.write_events(self.accepted_pair("g1", 1) + self.accepted_pair("g2", 3))
        self.assertEqual(self.run_check()[0], 0)
        self.assertEqual(self.run_check("--leg", "g1")[0], 0)
        self.assertEqual(self.run_check("--events")[0], 0)


if __name__ == "__main__":
    import unittest
    unittest.main()
