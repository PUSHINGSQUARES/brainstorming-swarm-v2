import unittest

from scripts.check_campaign import validate_campaign, validate_role_map
from tests.test_checker import CampaignCase


class RequiredEffortTests(CampaignCase):
    def test_unavailable_required_effort(self):
        campaign = self.campaign()
        campaign["roles"][0].update(required={"effort": True}, observed_availability={"model": "available", "effort": "unavailable"})
        self.assertIn("required effort", " ".join(validate_role_map(campaign)))
        self.save_campaign(campaign)
        self.assertIn("required effort", " ".join(validate_campaign(self.root)))

    def test_unverified_required_effort(self):
        campaign = self.campaign()
        campaign["roles"][0].update(required={"effort": True}, observed_availability={"model": "available", "effort": "unknown"})
        errors = " ".join(validate_role_map(campaign))
        self.assertIn("required effort availability is unverified", errors)
        self.save_campaign(campaign)
        self.assertIn("required effort availability is unverified", " ".join(validate_campaign(self.root)))


if __name__ == "__main__":
    unittest.main()
