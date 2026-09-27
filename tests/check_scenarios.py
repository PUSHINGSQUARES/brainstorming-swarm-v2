"""Check four recorded decision invariants in synthetic scenario fixtures."""
import hashlib
import json
import sys
from pathlib import Path

SCENARIOS = {"material-revision", "incomplete-leg", "digest-revision", "prd-review-gate"}
ROOT = Path(__file__).parent / "fixtures" / "scenarios"


def _artifact(fixture, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        return None
    root = fixture.parent.resolve()
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        return None
    return resolved.read_bytes()


def _matches(fixture, record):
    content = _artifact(fixture, record["artifact"])
    return content is not None and hashlib.sha256(content).hexdigest() == record["sha256"]


def check(scenario, path):
    fixture = Path(path)
    data = json.loads(fixture.read_text(encoding="utf-8"))
    if scenario == "material-revision":
        old, new = data["drafts"]
        prior, current = data["judges"]
        return (old["revision"] == 1 and new["revision"] == 2
                and old["artifact"] != new["artifact"]
                and new["supersedes"] == old["artifact"]
                and _matches(fixture, old) and _matches(fixture, new)
                and prior["target_artifact"] == old["artifact"]
                and prior["target_sha256"] == old["sha256"]
                and prior["state"] == "invalidated"
                and current["judge_id"] != prior["judge_id"]
                and current["target_artifact"] == new["artifact"]
                and current["target_sha256"] == new["sha256"]
                and current["state"] == "current"
                and data["synthesis"]["adopted_judge_id"] == current["judge_id"]
                and data["synthesis"]["adopted_draft_artifact"] == new["artifact"])
    if scenario == "incomplete-leg":
        accepted = set(data["synthesis_accepted_leg_ids"])
        statuses = {leg["leg_id"]: leg["status"] for leg in data["legs"]}
        return bool(accepted) and accepted.issubset(statuses) and all(statuses[leg_id] == "accepted" for leg_id in accepted)
    if scenario == "digest-revision":
        old, new = data["revisions"]
        ledger = _artifact(fixture, data["ledger"])
        return (old["revision"] == 1 and new["revision"] == 2
                and old["artifact"] != new["artifact"]
                and _matches(fixture, old) and _matches(fixture, new)
                and old["sha256"] != new["sha256"]
                and new["supersedes"] == old["artifact"]
                and ledger is not None
                and old["artifact"].encode() in ledger and new["artifact"].encode() in ledger
                and bool(data["dissent"])
                and all(item.encode() in ledger for item in data["dissent"]))
    if scenario == "prd-review-gate":
        return (data["design_approval"] == "approved"
                and data["written_prd_review"] == "approved"
                and type(data["prd_review_order"]) is int
                and type(data["task_plan_order"]) is int
                and data["prd_review_order"] < data["task_plan_order"])
    raise ValueError(scenario)


def main(argv):
    if not argv or argv[0] not in SCENARIOS or len(argv) > 2:
        print("Choose exactly one: " + ", ".join(sorted(SCENARIOS)), file=sys.stderr)
        return 2
    name = argv[0]
    path = Path(argv[1]) if len(argv) == 2 else ROOT / (name + ".json")
    try:
        ok = check(name, path)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print(f"{name}: invalid fixture: {exc}", file=sys.stderr)
        return 1
    print(f"{name}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
