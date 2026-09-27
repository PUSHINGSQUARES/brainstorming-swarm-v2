import unittest

from scripts.check_campaign import validate_campaign
from tests.test_checker import CampaignCase


class MissingJudgeTests(CampaignCase):
    def test_approach_without_judge_row_is_incomplete(self):
        campaign = self.campaign()
        campaign["approaches"] = [{"approach_id": "a1", "author_leg_id": "g1"}]
        self.save_campaign(campaign)
        errors = " ".join(validate_campaign(self.root))
        self.assertIn("approach a1 incomplete", errors)
        self.assertNotIn("kill", errors)

    def test_missing_judge_is_incomplete_not_kill(self):
        campaign = self.campaign()
        campaign["approaches"] = [{"approach_id": "a1", "author_leg_id": "g1"}]
        campaign["roles"].append({"leg_id": "j1", "role": "judge", "host": "example-host", "model": "session-default", "effort": "session-default", "source_of_choice": "session", "required": False, "observed_availability": "available", "routing_reason": "Review", "artifact": "digests/j1.json", "status": "accepted"})
        self.save_campaign(campaign)
        errors = " ".join(validate_campaign(self.root))
        self.assertIn("incomplete", errors)
        self.assertNotIn("kill", errors)


if __name__ == "__main__":
    unittest.main()
