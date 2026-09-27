import unittest

from scripts.check_campaign import validate_campaign, validate_role_map
from tests.test_checker import CampaignCase


class RequiredModelTests(CampaignCase):
    def test_unavailable_required_model(self):
        campaign = self.campaign()
        campaign["roles"][0].update(required=True, observed_availability="unavailable")
        self.assertIn("required model", " ".join(validate_role_map(campaign)))
        self.save_campaign(campaign)
        self.assertIn("required model", " ".join(validate_campaign(self.root)))

    def test_unverified_required_model(self):
        campaign = self.campaign()
        campaign["roles"][0].update(required={"model": True}, observed_availability={"model": "unknown", "effort": "available"})
        errors = " ".join(validate_role_map(campaign))
        self.assertIn("required model availability is unverified", errors)
        self.save_campaign(campaign)
        self.assertIn("required model availability is unverified", " ".join(validate_campaign(self.root)))


if __name__ == "__main__":
    unittest.main()
