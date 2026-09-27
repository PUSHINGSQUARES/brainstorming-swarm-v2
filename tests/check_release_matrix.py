"""Check exact support tuples and receipt expiry without inferring live support."""
import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re

try:
    from tests.check_live_receipts import public_path, validate_receipt
except ModuleNotFoundError:
    from check_live_receipts import public_path, validate_receipt

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"Claude": "Opus 5.5", "Codex": "GPT-6 Sol", "Grok": "Grok 4.7", "Muse": "Unverified"}
FIELDS = "host target_model status host_version model_id probe_date model_control effort_control receipt".split()


def read_rows(path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if cells[0] in {"Host", "---"}:
            continue
        if len(cells) != len(FIELDS):
            raise ValueError("matrix table must have nine columns")
        match = re.fullmatch(r"\[[^\]]+\]\(([^)]+)\)", cells[-1])
        if match:
            cells[-1] = match.group(1)
        rows.append(dict(zip(FIELDS, cells)))
    return rows


def validate_row(row, root, today=None):
    today = today or datetime.now(timezone.utc).date()
    errors = []
    if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k] for k in FIELDS):
        return ["matrix row requires all nine fields"]
    if row["status"] not in {"candidate", "unavailable", "tested"}:
        return ["support status must be candidate, unavailable, or tested"]
    if row["status"] != "tested":
        return errors
    for field in ("host_version", "model_id", "target_model"):
        if row[field].lower() in {"unverified", "unknown", "none", "session-default"}:
            errors.append("tested row needs exact " + field)
    try:
        probe = date.fromisoformat(row["probe_date"])
        age = (today - probe).days
        if age > 90:
            errors.append("probe is older than 90 days")
        if age < 0:
            errors.append("probe date is in the future")
    except ValueError:
        errors.append("tested row needs a valid probe date")
    try:
        receipt = json.loads(public_path(root, row["receipt"]).read_text())
    except (ValueError, OSError):
        return errors + ["tested row needs a linked evidence receipt"]
    if not isinstance(receipt, dict):
        return errors + ["receipt must be an object"]
    for key in ("host", "host_version", "target_model", "model_id", "probe_date"):
        if receipt.get(key) != row[key]:
            errors.append("receipt " + key + " does not match matrix")
    errors.extend(validate_receipt(receipt, root))
    return errors


def validate_matrix(root, today=None):
    try:
        rows = read_rows(root / "SUPPORT.md")
    except (ValueError, OSError):
        return ["cannot read the support matrix"]
    errors = []
    if len(rows) != 4 or sorted(row["host"] for row in rows) != sorted(TARGETS):
        errors.append("matrix must contain exactly one row per named host")
    for row in rows:
        host = row["host"]
        # Muse's model is unresolved until a live host provides its exact name.
        if host in TARGETS and host != "Muse" and row["target_model"] != TARGETS[host]:
            errors.append("named target model does not match host")
        errors.extend(validate_row(row, root, today))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = validate_matrix(args.root.resolve())
    for error in errors:
        print("FAIL: " + error)
    if not errors:
        print("PASS: four honest support rows; candidate is not live proof")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
