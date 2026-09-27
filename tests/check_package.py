"""Require the public skill, examples, checks, support guide, and release license."""

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "SKILL.md", "README.md", "LICENSE", "SUPPORT.md",
    "references/method.md", "references/journal.md",
    "references/host-guides/claude.md",
    "references/host-guides/codex.md",
    "references/host-guides/grok.md",
    "references/host-guides/muse.md",
    "templates/scope.md", "templates/role-map.json", "templates/gather.json",
    "templates/draft.json", "templates/judge.json", "templates/synthesis.json",
    "templates/ledger.md", "scripts/check_campaign.py",
    "examples/complete/campaign.json", "examples/no-spawn/campaign.json",
    "examples/partial-result/campaign.json",
    "tests/check_examples.py", "tests/check_scenarios.py",
    "tests/check_host_guides.py", "tests/check_release_matrix.py",
    "tests/check_live_receipts.py", "tests/check_public_tokens.py",
    "tests/check_public_surface.py", "evidence/README.md",
    "evidence/scrub-summary.md",
)


def missing_files(root):
    return [name for name in REQUIRED_FILES if not (root / name).is_file()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    missing = missing_files(args.root.resolve())
    for name in missing:
        print("MISSING: " + name)
    if not missing:
        print("PASS: public package contains every required file")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
