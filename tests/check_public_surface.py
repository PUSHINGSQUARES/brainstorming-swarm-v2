"""Check public paths and credential-shaped material without printing values."""

import argparse
import codecs
import re
from pathlib import Path
import subprocess

from check_public_tokens import NonTextFileError, ROOT, public_files, safe_file_id, text_lines


PATH_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:/(?:Volumes|Users|home|root)/[A-Za-z0-9_. -]+"
    r"|[A-Z]:\\Users\\[A-Za-z0-9_. -]+)"
)
CREDENTIAL_RES = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password|client[_-]?secret)\b['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_+/=-]{16,}"),
)


def findings_in_lines(lines, expressions):
    return [number for number, line in enumerate(lines, 1)
            if any(expression.search(line) for expression in expressions)]


def current_findings(root, expressions):
    findings = []
    for path in public_files(root):
        name = path.relative_to(root).as_posix()
        if any(expression.search(name) for expression in expressions):
            findings.append((name, 0))
        for number in findings_in_lines(text_lines(path), expressions):
            findings.append((name, number))
    return findings


def history_text(blob, kind):
    if kind == "tree":
        return blob.decode("latin1")
    if blob.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return blob.decode("utf-16")
    if b"\0" in blob:
        if len(blob) % 2 == 0:
            pairs = len(blob) // 2
            even_nulls = blob[0::2].count(0)
            odd_nulls = blob[1::2].count(0)
            if odd_nulls > pairs // 4 and even_nulls < pairs // 10:
                return blob.decode("utf-16-le")
            if even_nulls > pairs // 4 and odd_nulls < pairs // 10:
                return blob.decode("utf-16-be")
        raise NonTextFileError("undecodable historical object")
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError as error:
        raise NonTextFileError("undecodable historical object") from error


def history_findings(root):
    listing = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)"],
        capture_output=True, check=True, text=True,
    )
    findings = []
    for row in listing.stdout.splitlines():
        oid, kind = row.split(" ", 1)
        if kind not in {"blob", "commit", "tag", "tree"}:
            continue
        blob = subprocess.run(["git", "-C", str(root), "cat-file", kind, oid],
                              capture_output=True, check=True).stdout
        lines = history_text(blob, kind).splitlines()
        for number in findings_in_lines(lines, CREDENTIAL_RES):
            findings.append((oid, number))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("paths")
    credentials = sub.add_parser("credentials")
    credentials.add_argument("--history", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.mode == "paths":
            findings = [("PATH", name, number) for name, number in current_findings(root, (PATH_RE,))]
        else:
            findings = [("CREDENTIAL", name, number) for name, number in current_findings(root, CREDENTIAL_RES)]
            if args.history:
                findings.extend(("HISTORY CREDENTIAL", oid, number) for oid, number in history_findings(root))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("ERROR: public surface scan requires review (" + type(error).__name__ + ")")
        return 2
    for kind, name, number in findings:
        label = name if kind == "HISTORY CREDENTIAL" else safe_file_id(name)
        print(f"{kind}: {label}:{number}")
    if not findings:
        if args.mode == "paths":
            print("PASS: no operator paths found")
        elif args.history:
            print("PASS: no credential-shaped material in current files or Git objects")
        else:
            print("PASS: no credential-shaped material in current files")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
