"""Scan public candidate text for a private list of literal tokens."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


class NonTextFileError(ValueError):
    """A public candidate needs explicit review before release."""


def public_files(root):
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True, check=True,
    )
    names = {Path(item.decode("utf-8", "surrogateescape")) for item in result.stdout.split(b"\0") if item}
    for directory, child_dirs, files in os.walk(root, followlinks=False):
        child_dirs[:] = [name for name in child_dirs if name != ".git"]
        for name in files:
            if name == ".env" or name.startswith(".env.") or name.endswith((".pem", ".key")):
                names.add((Path(directory) / name).relative_to(root))
    return sorted(
        (root / name for name in names
         if (root / name).is_file() or (root / name).is_symlink()),
        key=lambda path: path.as_posix(),
    )


def text_lines(path):
    data = str(path.readlink()).encode("utf-8") if path.is_symlink() else path.read_bytes()
    if b"\0" in data:
        raise NonTextFileError("binary candidate")
    try:
        return data.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise NonTextFileError("undecodable candidate") from error


def load_patterns(path):
    if not path.is_file():
        raise ValueError("private pattern file is missing")
    patterns = [line.strip().casefold() for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
    if not patterns:
        raise ValueError("private pattern file contains no patterns")
    return patterns


def scan(root, patterns):
    findings = []
    for path in public_files(root):
        name = path.relative_to(root).as_posix()
        if any(pattern in name.casefold() for pattern in patterns):
            findings.append((name, 0))
        for number, line in enumerate(text_lines(path), 1):
            if any(pattern in line.casefold() for pattern in patterns):
                findings.append((name, number))
    return findings


def safe_file_id(name):
    return "file#" + hashlib.sha256(name.encode("utf-8", "surrogateescape")).hexdigest()[:12]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--patterns", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        findings = scan(args.root.resolve(), load_patterns(args.patterns))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("ERROR: token scan requires review (" + type(error).__name__ + ")")
        return 2
    for name, number in findings:
        print(f"TOKEN: {safe_file_id(name)}:{number}")
    if not findings:
        print("PASS: no private tokens in public candidate text")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
