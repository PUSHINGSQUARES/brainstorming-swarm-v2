import json
import unittest

from scripts.check_campaign import validate_campaign
from tests.test_checker import CampaignCase


class JudgeIndependenceTests(CampaignCase):
    def test_author_cannot_judge_own_approach(self):
        campaign = self.campaign()
        campaign["approaches"] = [{"approach_id": "a1", "author_leg_id": "g1"}]
        campaign["roles"][0]["role"] = "judge"
        self.save_campaign(campaign)
        (self.root / "digests" / "g1.json").write_text(json.dumps({"leg_id": "g1", "host": "example-host", "model": "session-default", "effort": "session-default", "role": "judge", "artifact": "digests/g1.json", "target_id": "a1", "judge_leg_id": "g1", "verdict": "keep", "severity": "low", "counterevidence": [], "keep_clauses": []}))
        errors = " ".join(validate_campaign(self.root))
        self.assertIn("author cannot judge own approach: a1", errors)
        self.assertNotIn("judge_leg_id does not match role", errors)


if __name__ == "__main__":
    unittest.main()
