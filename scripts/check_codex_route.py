"""Check a child route against one local Codex desktop session record.

This is a host-side preflight, not backend model attestation. It relies on the
current Codex JSONL record shape and fails closed when that shape is uncertain.
"""

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from uuid import UUID


MAX_ROLLOUT_BYTES = 32 * 1024 * 1024
MAX_LINE_BYTES = 4 * 1024 * 1024
MAX_RECORDS = 100_000


class RouteError(Exception):
    """A route cannot be verified from the local session record."""


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _matching_rollout(root, thread_id):
    if not root.is_dir():
        raise RouteError("session root unavailable")
    matches = []
    walk_errors = []

    def on_error(_error):
        walk_errors.append(True)

    for directory, subdirs, files in os.walk(root, onerror=on_error, followlinks=False):
        subdirs[:] = [name for name in subdirs if not (Path(directory) / name).is_symlink()]
        for name in files:
            if name == thread_id + ".jsonl" or name.endswith("-" + thread_id + ".jsonl"):
                matches.append(Path(directory) / name)
    if walk_errors:
        raise RouteError("session search incomplete")
    if len(matches) != 1:
        raise RouteError("expected exactly one matching rollout")
    if matches[0].is_symlink() or not matches[0].is_file():
        raise RouteError("matching rollout unavailable")
    return matches[0]


def _open_rollout(root, rollout):
    """Open the selected file without following any component below the root."""
    if (not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY") or
            not hasattr(os, "O_NONBLOCK") or
            not hasattr(os, "supports_dir_fd") or os.open not in os.supports_dir_fd):
        raise RouteError("safe descriptor traversal unavailable")
    try:
        parts = rollout.relative_to(root).parts
    except ValueError:
        raise RouteError("matching rollout outside session root")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise RouteError("invalid rollout path")

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    directory_fd = os.open(root, directory_flags)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(parts[-1], file_flags, dir_fd=directory_fd)
        try:
            opened = os.fstat(file_fd)
            if not stat.S_ISREG(opened.st_mode):
                raise RouteError("matching rollout is not a regular file")
            if opened.st_size > MAX_ROLLOUT_BYTES:
                raise RouteError("rollout exceeds size limit")
            return file_fd
        except BaseException:
            os.close(file_fd)
            raise
    finally:
        os.close(directory_fd)


def verify_route(thread_id, expected_model, expected_effort, session_root):
    """Verify exact local session identity and every recorded turn context."""
    try:
        if str(UUID(thread_id)) != thread_id:
            raise ValueError("noncanonical UUID")
    except (TypeError, ValueError, AttributeError):
        raise RouteError("invalid child thread ID")
    if not expected_model or not expected_effort:
        raise RouteError("expected model and effort are required")

    rollout = _matching_rollout(Path(session_root), thread_id)
    metadata_count = 0
    context_count = 0
    try:
        file_fd = _open_rollout(Path(session_root), rollout)
        try:
            stream = os.fdopen(file_fd, "rb")
        except BaseException:
            os.close(file_fd)
            raise
        with stream:
            total_bytes = 0
            record_count = 0
            while True:
                line = stream.readline(MAX_LINE_BYTES + 1)
                if not line:
                    break
                total_bytes += len(line)
                record_count += 1
                if len(line) > MAX_LINE_BYTES:
                    raise RouteError("rollout line exceeds size limit")
                if total_bytes > MAX_ROLLOUT_BYTES or record_count > MAX_RECORDS:
                    raise RouteError("rollout exceeds size or record limit")
                entry = json.loads(line.decode("utf-8"), object_pairs_hook=_unique_keys)
                if not isinstance(entry, dict) or not isinstance(entry.get("type"), str):
                    raise RouteError("malformed session record")
                kind = entry["type"]
                if kind not in {"session_meta", "turn_context"}:
                    continue
                payload = entry.get("payload")
                if not isinstance(payload, dict):
                    raise RouteError("malformed route record")
                if kind == "session_meta":
                    metadata_count += 1
                    if metadata_count != 1 or payload.get("id") != thread_id:
                        raise RouteError("session identity missing or inconsistent")
                else:
                    context_count += 1
                    if payload.get("model") != expected_model or payload.get("effort") != expected_effort:
                        raise RouteError("turn context route mismatch")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError):
        raise RouteError("rollout unreadable or malformed")
    if metadata_count != 1 or context_count < 1:
        raise RouteError("required route records missing")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("thread_id", help="Explicit child thread UUID")
    parser.add_argument("expected_model", help="Exact requested model ID")
    parser.add_argument("expected_effort", help="Exact requested reasoning effort")
    parser.add_argument(
        "--session-root", type=Path, default=Path.home() / ".codex" / "sessions",
        help="Codex sessions directory (defaults to the current user's home)",
    )
    args = parser.parse_args(argv)
    try:
        verify_route(args.thread_id, args.expected_model, args.expected_effort, args.session_root)
    except RouteError as error:
        print("route preflight failed: %s" % error, file=sys.stderr)
        return 1
    print("local route evidence: thread=%s model=%s effort=%s" % (
        args.thread_id, args.expected_model, args.expected_effort,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
