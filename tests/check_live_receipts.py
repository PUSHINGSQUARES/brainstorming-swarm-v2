"""Validate sanitized native-event receipts; never infer that live events occurred."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LIMITS = "Structure and artifact hashes only. Raw-event authenticity, independent review, and reasoning quality need separate audits."
TERMINAL = {"completed", "failed", "cancelled", "termination_unknown"}
PROBES = {"missing", "malformed", "deadline", "cancel"}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp needs a timezone")
    try:
        return parsed.astimezone(timezone.utc)
    except OverflowError:
        raise ValueError("timestamp lies outside supported UTC range") from None


def public_path(root, value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("path must be relative")
    path = Path(value)
    if not path.parts or path.is_absolute() or ".." in path.parts or path.parts[0] != "evidence":
        raise ValueError("path must stay under evidence")
    resolved = (root / path).resolve()
    try:
        resolved.relative_to((root / "evidence").resolve())
        resolved.relative_to(root.resolve())
    except ValueError:
        raise ValueError("path escapes evidence")
    return resolved


def label(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._+/:-]{0,127}", value)) and value.lower() not in {"unknown", "unverified", "session-default"}


def events(value):
    return isinstance(value, list) and bool(value) and len(set(x for x in value if isinstance(x, str))) == len(value) and all(isinstance(x, str) and re.fullmatch(r"evt-[a-z0-9]{4,64}", x) for x in value)


def overlapped(a, b):
    return a["child_id"] != b["child_id"] and max(timestamp(a["start"]), timestamp(b["start"])) < min(timestamp(a["end"]), timestamp(b["end"]))


def _keys(value, expected, errors, context):
    if not isinstance(value, dict):
        errors.append(context + " must be an object")
        return False
    if set(value) != set(expected.split()):
        errors.append(context + " has missing or unsupported fields")
    return True


def validate_receipt(receipt, root):
    """Both command modes apply the full contract to prevent partial proof promotion."""
    errors = []
    if not _keys(receipt, "schema_version host host_version target_model model_id probe_date effort_exposed children lifecycle_probes", errors, "receipt"):
        return errors
    if type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1:
        errors.append("schema_version must be 1")
    for field in ("host", "host_version", "target_model", "model_id"):
        if not label(receipt.get(field)):
            errors.append(field + " needs an observed identity")
    try:
        probe_date = datetime.strptime(receipt.get("probe_date", ""), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        probe_date = None
        errors.append("probe_date must be an ISO date")
    exposed = receipt.get("effort_exposed")
    if type(exposed) is not bool:
        errors.append("effort_exposed must be a boolean")
    children = receipt.get("children")
    if not isinstance(children, list) or len(children) < 2:
        errors.append("two or more child receipts are required")
        children = []
    child_ids, artifact_paths, valid_intervals = [], [], []
    all_event_ids = []
    for index, child in enumerate(children):
        context = "child %s" % index
        if not _keys(child, "child_id start end reported_model_id model_source requested_effort reported_effort terminal_state artifact raw_event_ids", errors, context):
            continue
        child_id = child.get("child_id")
        if not isinstance(child_id, str) or not re.fullmatch(r"child-[a-z0-9-]{1,64}", child_id):
            errors.append(context + " needs an opaque child_id")
        else:
            child_ids.append(child_id)
        try:
            start, end = timestamp(child.get("start")), timestamp(child.get("end"))
            if start >= end:
                raise ValueError("invalid interval")
            if probe_date != start.date():
                errors.append(context + " start does not match probe_date")
            if isinstance(child_id, str) and re.fullmatch(r"child-[a-z0-9-]{1,64}", child_id):
                valid_intervals.append(child)
        except (ValueError, TypeError):
            errors.append(context + " needs an increasing timezone-aware start/end pair")
        if child.get("model_source") != "host" or child.get("reported_model_id") != receipt.get("model_id") or not label(child.get("reported_model_id")):
            errors.append(context + " model identity must match a host-reported model ID")
        if exposed is True:
            if not label(child.get("requested_effort")) or child.get("reported_effort") != child.get("requested_effort"):
                errors.append(context + " requested and reported effort must match")
        elif exposed is False and (child.get("requested_effort") is not None or child.get("reported_effort") is not None):
            errors.append(context + " unexposed effort must be null")
        if child.get("terminal_state") != "completed":
            errors.append(context + " successful overlap child must be completed")
        if not events(child.get("raw_event_ids")) or len(child.get("raw_event_ids", [])) < 2:
            errors.append(context + " needs distinct opaque start and result event IDs")
        if events(child.get("raw_event_ids")):
            all_event_ids.extend(child["raw_event_ids"])
        artifact = child.get("artifact")
        if _keys(artifact, "path sha256", errors, context + " artifact"):
            try:
                path = public_path(root, artifact.get("path"))
                artifact_paths.append(path)
                digest = artifact.get("sha256")
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise ValueError("invalid hash")
                if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    raise ValueError("hash mismatch")
            except (ValueError, OSError):
                errors.append(context + " artifact path or SHA256 does not verify")
    if len(set(child_ids)) != len(children):
        errors.append("child IDs must be distinct")
    if len(set(artifact_paths)) != len(children):
        errors.append("children need separate artifact paths")
    if not any(overlapped(a, b) for i, a in enumerate(valid_intervals) for b in valid_intervals[i + 1:]):
        errors.append("no two distinct child intervals strictly overlap")
    probes = receipt.get("lifecycle_probes")
    if not isinstance(probes, list):
        probes = []
    kinds = []
    for probe in probes:
        if not _keys(probe, "kind child_id terminal_state raw_event_ids", errors, "lifecycle probe"):
            continue
        kinds.append(probe.get("kind"))
        if not isinstance(probe.get("child_id"), str) or not re.fullmatch(r"child-[a-z0-9-]{1,64}", probe["child_id"]):
            errors.append("lifecycle probe needs an opaque child_id")
        if not isinstance(probe.get("terminal_state"), str) or probe["terminal_state"] not in TERMINAL:
            errors.append("lifecycle probe needs explicit terminal state or termination_unknown")
        if not events(probe.get("raw_event_ids")):
            errors.append("lifecycle probe needs opaque event IDs")
        else:
            all_event_ids.extend(probe["raw_event_ids"])
    if len(set(all_event_ids)) != len(all_event_ids):
        errors.append("raw event IDs must be unique across all child and lifecycle records")
    if sorted(str(k) for k in kinds) != sorted(PROBES):
        errors.append("exactly one missing, malformed, deadline, and cancel probe is required")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("overlap", "model-identity"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt", action="append", help="Receipt path relative to root; repeat for multiple files")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = []
    if args.receipt:
        paths = args.receipt
    else:
        # Only matrix-linked tested receipts count; no glob can collect synthetic proof.
        try:
            from tests.check_release_matrix import read_rows, validate_matrix
        except ModuleNotFoundError:
            from check_release_matrix import read_rows, validate_matrix
        errors.extend(validate_matrix(root))
        try:
            paths = [r["receipt"] for r in read_rows(root / "SUPPORT.md") if r["status"] == "tested"]
        except (OSError, ValueError):
            paths = []
    if not paths:
        errors.append("no tested receipts selected; live proof remains unverified")
    for number, value in enumerate(paths):
        try:
            receipt = json.loads(public_path(root, value).read_text())
            errors.extend("receipt %s: %s" % (number + 1, error) for error in validate_receipt(receipt, root))
        except (OSError, ValueError, TypeError):
            errors.append("receipt %s: cannot read a valid evidence receipt" % (number + 1))
    for error in errors:
        print("FAIL: " + error)
    if not errors:
        print("PASS: " + args.mode + " receipt structure")
    print(LIMITS)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
