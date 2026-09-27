"""Check guide presence and keep live claims tied to current support receipts."""

import argparse
from datetime import date
from pathlib import Path
import re

try:
    from tests.check_release_matrix import read_rows, validate_row
except ModuleNotFoundError:
    from check_release_matrix import read_rows, validate_row


ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"Claude": "claude.md", "Codex": "codex.md", "Grok": "grok.md", "Muse": "muse.md"}
CLAIM_PATTERNS = (
    re.compile(r"\b(?:we|this host|this guide|the run)\b[^.\n]{0,100}"
               r"\b(?:spawned|launched|completed|ran|verified)\b[^.\n]{0,90}"
               r"\b(?:two|2|multiple|independent)\s+(?:children|agents|legs|subagents)\b", re.I),
    re.compile(r"\b(?:two|2|the|multiple|independent)\s+(?:independent\s+)?"
               r"(?:children|agents|legs|subagents)\b[^.\n]{0,100}"
               r"\b(?:spawned|launched|completed|succeeded|overlapped)\b", re.I),
    re.compile(r"\b(?:a\s+)?(?:live|real|successful)\s+probe\b[^.\n]{0,80}"
               r"\b(?:confirmed|proved|verified)\b[^.\n]{0,80}"
               r"\b(?:children|agents|subagents|overlapp\w*)\b", re.I),
)
NEGATION = re.compile(r"\b(?:no|not|never|cannot|can't|without|unverified|unknown|unsupported)\b", re.I)
CARD_LINE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$", re.M)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def candidate_claims_live_success(content):
    """Catch common asserted child-run claims; semantic review remains required."""
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", content):
        for pattern in CLAIM_PATTERNS:
            match = pattern.search(sentence)
            if match and not NEGATION.search(sentence[:match.end()]):
                return True
    return False


def observation_card(content):
    if "## Host Observation" not in content:
        return {}
    section = content.split("## Host Observation", 1)[1].split("##", 1)[0]
    return {key.strip().lower(): value.strip() for key, value in CARD_LINE.findall(section)}


def validate_guides(root, today=None):
    """Return errors rather than turning missing public files into tracebacks."""
    today = today or date.today()
    try:
        rows = read_rows(root / "SUPPORT.md")
    except (OSError, ValueError):
        return ["cannot read support matrix"]
    by_host = {row["host"]: row for row in rows}
    errors = []
    for host, filename in HOSTS.items():
        guide = root / "references" / "host-guides" / filename
        try:
            content = guide.read_text()
        except OSError:
            errors.append(f"{host}: missing host guide")
            continue
        row = by_host.get(host)
        if row is None:
            errors.append(f"{host}: missing support row")
            continue
        card = observation_card(content)
        status_match = re.match(r"`?(candidate|tested|unavailable)`?\b", card.get("support status", ""), re.I)
        if not status_match:
            errors.append(f"{host}: missing Support status card field")
            continue
        guide_status = status_match.group(1).lower()
        matrix_status = row["status"]
        if guide_status != matrix_status:
            errors.append(f"{host}: guide and matrix status disagree")
        if matrix_status == "candidate":
            if candidate_claims_live_success(content):
                errors.append(f"{host}: candidate guide claims a successful child spawn")
            if row["receipt"] != "none":
                errors.append(f"{host}: candidate row must not link tested proof")
        elif matrix_status == "tested":
            errors.extend(f"{host}: {error}" for error in validate_row(row, root, today))
            for field, expected in (("live host version", row["host_version"]),
                                    ("live model id", row["model_id"]),
                                    ("live probe date", row["probe_date"])):
                if card.get(field) != expected:
                    errors.append(f"{host}: tested guide {field} does not match matrix")
            link = MARKDOWN_LINK.fullmatch(card.get("live receipt", ""))
            if (not link or Path(link.group(1)).is_absolute()
                    or (guide.parent / link.group(1)).resolve() != (root / row["receipt"]).resolve()):
                errors.append(f"{host}: tested guide must link its matching receipt")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = validate_guides(args.root.resolve())
    for error in errors:
        print("FAIL: " + error)
    if not errors:
        print("PASS: four host guides match current support evidence")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
