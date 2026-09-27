import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_campaign import LIMITS, main, validate_campaign


FIXTURE = Path(__file__).parent / "fixtures" / "valid"


class CampaignCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "campaign"
        shutil.copytree(FIXTURE, self.root)

    def campaign(self):
        return json.loads((self.root / "campaign.json").read_text())

    def save_campaign(self, campaign):
        (self.root / "campaign.json").write_text(json.dumps(campaign))


class CheckerTests(CampaignCase):
    def test_valid_campaign_and_limits(self):
        self.assertEqual(validate_campaign(self.root), [])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn(LIMITS, output.getvalue())

    def test_limits_on_failure(self):
        (self.root / "digests" / "g1.json").unlink()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(self.root)])
        self.assertNotEqual(code, 0)
        self.assertIn(LIMITS, output.getvalue())


if __name__ == "__main__":
    unittest.main()
