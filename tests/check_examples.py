"""Check solo and timeout examples retain honest outcome labels."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "examples"


def check(name, root):
    if name == "no-spawn":
        campaign = json.loads((root / "no-spawn" / "campaign.json").read_text())
        ledger = (root / "no-spawn" / "ledger.md").read_text()
        return campaign["status"] == "solo_analysis" and "solo_analysis" in ledger and not campaign["synthesis"]["accepted_leg_ids"]
    if name == "timeout":
        campaign = json.loads((root / "partial-result" / "campaign.json").read_text())
        ledger = (root / "partial-result" / "ledger.md").read_text()
        roles = {r["leg_id"]: r["status"] for r in campaign["roles"]}
        accepted = set(campaign["synthesis"]["accepted_leg_ids"])
        lifecycle = campaign["lifecycle"]
        timeout = lifecycle["child-timeout"]
        missing = lifecycle["judge-missing"]
        return (roles.get("judge-missing") == "incomplete"
                and roles.get("child-timeout") == "termination_unknown"
                and "incomplete" in ledger and "termination_unknown" in ledger
                and "stop receipt" in ledger
                and missing["artifact_received"] is False
                and not (root / "partial-result" / "digests" / "judge-missing.json").exists()
                and timeout["deadline_expired"] is True
                and timeout["stop_requested"] is True
                and timeout["stop_confirmed"] is False
                and timeout["stop_receipt"] is None
                and not ({"judge-missing", "child-timeout"} & accepted))
    raise ValueError(name)


def main(argv):
    if not argv or argv[0] not in {"no-spawn", "timeout"} or len(argv) > 2:
        print("Choose no-spawn or timeout", file=sys.stderr)
        return 2
    root = Path(argv[1]) if len(argv) == 2 else ROOT
    try:
        ok = check(argv[0], root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"{argv[0]}: invalid example: {exc}", file=sys.stderr)
        return 1
    print(f"{argv[0]}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
