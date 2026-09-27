import json
import contextlib
import io
import unittest

from scripts.check_campaign import LIMITS, main, validate_campaign
from tests.test_checker import CampaignCase, FIXTURE


class NegativeCampaignTests(CampaignCase):
    def assert_structured_failure(self, expected):
        errors = " ".join(validate_campaign(self.root))
        self.assertIn(expected, errors)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn(LIMITS, output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_missing_root_fields(self):
        for key in ("campaign_id", "ledger", "synthesis"):
            with self.subTest(key=key):
                campaign = self.campaign()
                campaign.pop(key)
                self.save_campaign(campaign)
                self.assert_structured_failure(key)
                self.save_campaign({**campaign, key: json.loads((FIXTURE / "campaign.json").read_text())[key]})

    def test_empty_roles_rejected(self):
        campaign = self.campaign()
        campaign["roles"] = []
        self.save_campaign(campaign)
        self.assert_structured_failure("roles must not be empty")

    def test_invalid_campaign_status(self):
        campaign = self.campaign()
        campaign["status"] = "complete"
        self.save_campaign(campaign)
        self.assert_structured_failure("campaign.status")

    def test_invalid_required_shape(self):
        campaign = self.campaign()
        campaign["roles"][0]["required"] = "yes"
        self.save_campaign(campaign)
        self.assert_structured_failure("required must be a boolean or model/effort object")

    def test_invalid_availability_shape(self):
        campaign = self.campaign()
        campaign["roles"][0]["observed_availability"] = "bogus"
        self.save_campaign(campaign)
        self.assert_structured_failure("observed_availability")

    def test_unhashable_approach_author(self):
        campaign = self.campaign()
        campaign["approaches"] = [{"approach_id": "a1", "author_leg_id": []}]
        self.save_campaign(campaign)
        self.assert_structured_failure("author_leg_id")

    def test_unhashable_accepted_leg(self):
        campaign = self.campaign()
        campaign["synthesis"]["accepted_leg_ids"] = [{}]
        self.save_campaign(campaign)
        self.assert_structured_failure("accepted_leg_ids")

    def test_unhashable_selected_approach(self):
        campaign = self.campaign()
        campaign["synthesis"]["selected_approach_id"] = []
        self.save_campaign(campaign)
        self.assert_structured_failure("selected_approach_id")

    def test_nul_artifact_path(self):
        campaign = self.campaign()
        campaign["roles"][0]["artifact"] = "bad\x00name.json"
        self.save_campaign(campaign)
        self.assert_structured_failure("invalid artifact path")

    def test_symlink_loop_artifact(self):
        loop = self.root / "digests" / "loop.json"
        loop.symlink_to(loop)
        campaign = self.campaign()
        campaign["roles"][0]["artifact"] = "digests/loop.json"
        self.save_campaign(campaign)
        self.assert_structured_failure("invalid artifact path")

    def test_unknown_role_with_matching_digest(self):
        campaign = self.campaign()
        campaign["roles"][0]["role"] = "bogus"
        self.save_campaign(campaign)
        digest_path = self.root / "digests" / "g1.json"
        digest = json.loads(digest_path.read_text())
        digest["role"] = "bogus"
        digest_path.write_text(json.dumps(digest))
        self.assertIn("role must be gather, draft, or judge", " ".join(validate_campaign(self.root)))

    def test_duplicate_leg_id(self):
        campaign = self.campaign()
        campaign["roles"][1]["leg_id"] = "g1"
        self.save_campaign(campaign)
        self.assertIn("duplicate leg_id", " ".join(validate_campaign(self.root)))

    def test_invalid_status(self):
        campaign = self.campaign()
        campaign["roles"][0]["status"] = "done"
        self.save_campaign(campaign)
        self.assertIn("status", " ".join(validate_campaign(self.root)))

    def test_nonexistent_artifact(self):
        campaign = self.campaign()
        campaign["roles"][0]["artifact"] = "digests/missing.json"
        self.save_campaign(campaign)
        self.assertIn("missing artifact", " ".join(validate_campaign(self.root)))

    def test_path_escape(self):
        campaign = self.campaign()
        campaign["roles"][0]["artifact"] = "../outside.json"
        self.save_campaign(campaign)
        self.assertIn("escapes campaign root", " ".join(validate_campaign(self.root)))

    def test_symlink_escape(self):
        campaign = self.campaign()
        outside = self.root.parent / "outside.json"
        outside.write_text("{}")
        (self.root / "digests" / "link.json").symlink_to(outside)
        campaign["roles"][0]["artifact"] = "digests/link.json"
        self.save_campaign(campaign)
        self.assertIn("escapes campaign root", " ".join(validate_campaign(self.root)))


if __name__ == "__main__":
    unittest.main()
