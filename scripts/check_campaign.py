"""Check campaign structure and local file presence without external services."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


VALID_KINDS = {"file", "url", "supplied"}
VALID_ROLES = {"gather", "draft", "judge"}
VALID_VERDICTS = {"keep", "revise", "kill"}
VALID_SEVERITIES = {"none", "minor", "major", "critical"}
VALID_STATUSES = {"accepted", "incomplete", "failed", "cancelled", "termination_unknown"}
VALID_CAMPAIGN_STATUSES = {"design_pending", "solo_analysis"}
VALID_AVAILABILITY = {"available", "unavailable", "unsupported", "unknown", "unverified"}
VALID_DEPENDENCY_STATUSES = {"supported", "unverified", "contradicted"}
LIMITS = "Structure and local presence only. Citation truth, author identity, reasoning quality, concurrency, cancellation, and freshness are unverified."
EVENT_LIMITS = "Journal order is local evidence only. Source truth, native start time, prior-byte preservation, and operator-supplied timestamps are unverified. With null sha256, artifact tampering cannot be checked."
MAX_EVENTS = 10000
MAX_EVENT_BYTES = 16384
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")
EVENT_FIELDS = {
    "validation": {"seq", "at", "type", "leg_id", "artifact", "sha256", "result", "checker", "source_review", "status_during_event"},
    "acceptance": {"seq", "at", "type", "leg_id", "artifact", "sha256", "validation_seq"},
    "correction": {"seq", "at", "type", "corrects_seq", "reason", "effect"},
    "revocation": {"seq", "at", "type", "leg_id", "acceptance_seq", "reason"},
}


def _filled(value):
    return isinstance(value, str) and bool(value.strip())


def validate_evidence(value):
    """Return structural errors for one typed evidence anchor."""
    if not isinstance(value, dict) or not _filled(value.get("kind")) or value["kind"] not in VALID_KINDS:
        return ["evidence.kind must be file, url, or supplied"]
    kind = value["kind"]
    required = {"file": ("path", "lines"), "url": ("url", "section"), "supplied": ("id",)}[kind]
    errors = []
    for key in required:
        item = value.get(key)
        if item is None or item == "" or item == [] or not isinstance(item, (str, list)):
            errors.append("evidence.%s is required" % key)
    if kind == "file" and "lines" in value:
        lines = value["lines"]
        if not (isinstance(lines, list) and len(lines) == 2 and all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in lines) and lines[0] <= lines[1]):
            errors.append("evidence.lines must be a positive [start, end] range")
    if kind == "url" and _filled(value.get("url")):
        try:
            parsed = urlsplit(value["url"])
            valid_url = (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                         and not any(char.isspace() for char in value["url"]))
        except ValueError:
            valid_url = False
        if not valid_url:
            errors.append("evidence.url must be an HTTP(S) URL")
    for key in ("path", "url", "section", "id"):
        if key in required and key in value and not _filled(value[key]):
            message = "evidence.%s is required" % key
            if message not in errors:
                errors.append(message)
    return errors


def _required(required, field):
    if isinstance(required, dict):
        return required.get(field) is True
    return required is True


def _availability_state(observed, field):
    if isinstance(observed, dict):
        observed = observed.get(field)
    if observed == "available":
        return "available"
    if observed in ("unavailable", "unsupported"):
        return "unavailable"
    return "unverified"


def _valid_required(value):
    return isinstance(value, bool) or (isinstance(value, dict) and
        set(value).issubset({"model", "effort"}) and
        all(isinstance(item, bool) for item in value.values()))


def _valid_availability(value):
    return (isinstance(value, str) and value in VALID_AVAILABILITY) or (
        isinstance(value, dict) and set(value).issubset({"model", "effort"}) and
        all(isinstance(item, str) and item in VALID_AVAILABILITY for item in value.values()))


def validate_role_map(campaign):
    """Check role rows and fail explicit requirements that cannot be met."""
    if not isinstance(campaign, dict) or not isinstance(campaign.get("roles"), list):
        return ["campaign.roles must be a list"]
    errors = []
    seen = set()
    for index, role in enumerate(campaign["roles"]):
        label = "roles[%d]" % index
        if not isinstance(role, dict):
            errors.append("%s must be an object" % label)
            continue
        leg_id = role.get("leg_id")
        if not _filled(leg_id):
            errors.append("%s.leg_id is required" % label)
        elif leg_id in seen:
            errors.append("duplicate leg_id: %s" % leg_id)
        else:
            seen.add(leg_id)
        for key in ("role", "host", "model", "effort", "source_of_choice", "routing_reason", "artifact"):
            if not _filled(role.get(key)):
                errors.append("%s.%s is required" % (label, key))
        if _filled(role.get("role")) and role["role"] not in VALID_ROLES:
            errors.append("%s.role must be gather, draft, or judge" % label)
        if not _filled(role.get("status")) or role["status"] not in VALID_STATUSES:
            errors.append("%s.status must be a valid leg status" % label)
        if "required" not in role or not _valid_required(role["required"]):
            errors.append("%s.required must be a boolean or model/effort object" % label)
        if "observed_availability" not in role or not _valid_availability(role["observed_availability"]):
            errors.append("%s.observed_availability must be an availability enum or model/effort object" % label)
        for field in ("model", "effort"):
            if _required(role.get("required"), field):
                availability = _availability_state(role.get("observed_availability"), field)
                if availability == "unavailable":
                    errors.append("%s required %s is unavailable" % (label, field))
                elif availability == "unverified":
                    errors.append("%s required %s availability is unverified" % (label, field))
    return errors


def _local_file(root, relative, label, missing_label):
    if not _filled(relative):
        return None, ["%s path is required" % label]
    try:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            return None, ["%s escapes campaign root: %s" % (label, relative)]
        unresolved = root / path
        resolved = unresolved.resolve()
        resolved.relative_to(root.resolve())
        try:
            resolved = unresolved.resolve(strict=True)
        except FileNotFoundError:
            return None, ["%s: %s" % (missing_label, relative)]
        resolved.relative_to(root.resolve())
    except ValueError:
        if "\x00" in relative:
            return None, ["invalid %s path" % label]
        return None, ["%s escapes campaign root: %s" % (label, relative)]
    except (OSError, RuntimeError):
        return None, ["invalid %s path" % label]
    try:
        exists = resolved.is_file()
    except (OSError, ValueError, RuntimeError):
        return None, ["invalid %s path" % label]
    if not exists:
        return None, ["%s: %s" % (missing_label, relative)]
    return resolved, []


def _read_json(path, label):
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, ["%s is invalid JSON: %s" % (label, exc)]
    if not isinstance(value, dict):
        return None, ["%s must be an object" % label]
    return value, []


def _event_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON field: %s" % key)
        value[key] = item
    return value


def _event_time(value):
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _event_hash_errors(event, label):
    digest = event.get("sha256")
    if isinstance(digest, str) and HASH_RE.fullmatch(digest):
        return ["%s hash_limit is only allowed with null sha256" % label] if "hash_limit" in event else []
    if digest is None:
        return [] if _filled(event.get("hash_limit")) else ["%s hash_limit is required with null sha256" % label]
    return ["%s sha256 must be 64 lowercase hex characters or null" % label]


def _bounded_journal_lines(stream):
    while True:
        raw = stream.readline(MAX_EVENT_BYTES + 1)
        if not raw:
            return
        if len(raw) > MAX_EVENT_BYTES and not raw.endswith(b"\n"):
            while raw and not raw.endswith(b"\n"):
                raw = stream.readline(MAX_EVENT_BYTES + 1)
            yield b" " * (MAX_EVENT_BYTES + 1)
        else:
            yield raw


def _retractable_validation_error(error, seq):
    """Only field-level defects in an unused, retracted validation are recoverable."""
    prefix = "events line %d " % seq
    if not error.startswith(prefix):
        return False
    detail = error[len(prefix):]
    return detail.startswith((
        "sha256 must", "hash_limit", "result must", "status_during_event must",
        "checker must", "source_review must",
    ))


def validate_events(root: Path, campaign, leg_id=None):
    """Validate the bounded physical journal and effective acceptance state."""
    if "events" not in campaign:
        return ["campaign.events is required for --events"]
    root = Path(root)
    journal, errors = _local_file(root, campaign.get("events"), "events", "missing events")
    if errors:
        return errors
    roles = campaign.get("roles")
    if not isinstance(roles, list):
        return ["campaign.roles must be a list"]
    role_by_id = {r["leg_id"]: r for r in roles if isinstance(r, dict) and _filled(r.get("leg_id"))}
    events = {}
    active = {}
    invalidated_validations = set()
    last_invalidation = {}
    latest_review = {}
    retracted_validations = set()
    acceptance_references = set()
    prior_time = None
    try:
        with journal.open("rb") as stream:
            for line_number, raw in enumerate(_bounded_journal_lines(stream), 1):
                label = "events line %d" % line_number
                if line_number > MAX_EVENTS:
                    errors.append("events exceeds %d lines" % MAX_EVENTS)
                    break
                if len(raw) > MAX_EVENT_BYTES:
                    errors.append("%s exceeds %d bytes" % (label, MAX_EVENT_BYTES))
                    continue
                if not raw.endswith(b"\n") or not raw.strip():
                    errors.append("%s must be a nonblank newline-terminated JSON object" % label)
                    continue
                try:
                    event = json.loads(raw.decode("utf-8"), object_pairs_hook=_event_object,
                                       parse_constant=lambda item: (_ for _ in ()).throw(ValueError("nonfinite JSON number")))
                except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
                    errors.append("%s invalid JSON: %s" % (label, exc))
                    continue
                if not isinstance(event, dict):
                    errors.append("%s must be an object" % label)
                    continue
                seq = event.get("seq")
                if type(seq) is not int or seq != line_number:
                    errors.append("%s seq must equal physical line number %d" % (label, line_number))
                kind = event.get("type")
                if not isinstance(kind, str) or kind not in EVENT_FIELDS:
                    errors.append("%s unknown event type" % label)
                    continue
                required = EVENT_FIELDS[kind]
                optional = {"hash_limit"} if kind in {"validation", "acceptance"} else set()
                for field in sorted(required - event.keys()):
                    errors.append("%s missing field: %s" % (label, field))
                for field in sorted(event.keys() - required - optional):
                    errors.append("%s unknown field: %s" % (label, field))
                if required - event.keys() or event.keys() - required - optional:
                    continue
                at = _event_time(event["at"])
                if at is None:
                    errors.append("%s at must be a valid UTC timestamp ending Z" % label)
                elif prior_time is not None and at < prior_time:
                    errors.append("%s at goes backwards; backdating cannot repair history" % label)
                at_valid = at is not None and (prior_time is None or at >= prior_time)
                if at is not None:
                    prior_time = at
                if type(seq) is not int or seq != line_number:
                    continue
                events[seq] = event
                if kind in {"validation", "acceptance"}:
                    leg = event["leg_id"]
                    if not _filled(leg) or leg not in role_by_id:
                        errors.append("%s leg_id has no role" % label)
                        events.pop(seq, None)
                        continue
                    artifact, issue = _local_file(root, event["artifact"], "event artifact", "missing event artifact")
                    errors.extend("%s: %s" % (label, item) for item in issue)
                    errors.extend(_event_hash_errors(event, label))
                    if event["sha256"] is None and _filled(event.get("hash_limit")) and "tampering cannot be checked" not in event["hash_limit"].lower():
                        errors.append("%s hash_limit must explicitly state that tampering cannot be checked" % label)
                    if kind == "validation":
                        if artifact is not None:
                            latest_review[(leg, event["artifact"])] = seq
                        if not isinstance(event["result"], str) or event["result"] not in {"pass", "fail"}:
                            errors.append("%s result must be pass or fail" % label)
                        if event["status_during_event"] != "incomplete":
                            errors.append("%s status_during_event must be incomplete" % label)
                        for field in ("checker", "source_review"):
                            if not _filled(event[field]):
                                errors.append("%s %s must be nonblank" % (label, field))
                        if _filled(event["source_review"]) and (
                            len(event["source_review"].strip()) < 20 or ":" not in event["source_review"]
                        ):
                            errors.append("%s source_review must name clause and source anchor work, not a generic review claim" % label)
                    else:
                        validation_seq = event["validation_seq"]
                        if type(validation_seq) is int:
                            acceptance_references.add(validation_seq)
                        validation = events.get(validation_seq) if type(validation_seq) is int else None
                        if validation is None or validation_seq >= seq or validation.get("type") != "validation":
                            errors.append("%s acceptance requires a preceding validation" % label)
                        elif validation.get("result") != "pass" or validation_seq in invalidated_validations:
                            errors.append("%s acceptance requires a passing validation" % label)
                        elif latest_review.get((leg, event["artifact"])) != validation_seq:
                            errors.append("%s acceptance cannot use an older pass after a newer validation of the same artifact" % label)
                        elif validation_seq <= last_invalidation.get(leg, 0):
                            errors.append("%s acceptance requires a fresh passing validation after revocation" % label)
                        elif any(validation.get(key) != event.get(key) for key in ("leg_id", "artifact", "sha256", "hash_limit")):
                            errors.append("%s acceptance must match validation leg, artifact, and SHA256" % label)
                        elif leg in active:
                            errors.append("%s leg already has an active acceptance" % label)
                        elif artifact is not None and leg in role_by_id:
                            active[leg] = event
                elif kind == "correction":
                    target_seq = event["corrects_seq"]
                    target = events.get(target_seq) if type(target_seq) is int else None
                    if target is None or target_seq >= seq:
                        errors.append("%s corrects_seq must name an earlier event" % label)
                        continue
                    if not _filled(event["reason"]):
                        errors.append("%s reason must be nonblank" % label)
                    if not isinstance(event["effect"], str) or event["effect"] not in {"annotation", "retract", "barrier_unproven"}:
                        errors.append("%s effect must be annotation, retract, or barrier_unproven" % label)
                        continue
                    if event["effect"] != "annotation":
                        if target["type"] not in {"validation", "acceptance"}:
                            errors.append("%s can invalidate only validation or acceptance" % label)
                            continue
                        target_leg = target["leg_id"]
                        if target["type"] == "validation":
                            invalidated_validations.add(target_seq)
                            if (event["effect"] == "retract" and _filled(event["reason"])
                                    and at_valid):
                                retracted_validations.add(target_seq)
                            if active.get(target_leg, {}).get("validation_seq") == target_seq:
                                active.pop(target_leg, None)
                        elif active.get(target_leg, {}).get("seq") == target_seq:
                            active.pop(target_leg, None)
                        last_invalidation[target_leg] = seq
                else:
                    leg = event["leg_id"]
                    acceptance_seq = event["acceptance_seq"]
                    if not _filled(leg) or leg not in role_by_id:
                        errors.append("%s leg_id has no role" % label)
                        events.pop(seq, None)
                        continue
                    if type(acceptance_seq) is not int or active.get(leg, {}).get("seq") != acceptance_seq:
                        errors.append("%s revocation must name the active acceptance" % label)
                    else:
                        active.pop(leg, None)
                        last_invalidation[leg] = seq
                    if not _filled(event["reason"]):
                        errors.append("%s reason must be nonblank" % label)
    except OSError as exc:
        errors.append("events could not be read: %s" % exc)
    for seq in retracted_validations - acceptance_references:
        errors = [error for error in errors if not _retractable_validation_error(error, seq)]
    for identifier, role in role_by_id.items():
        if leg_id is not None and identifier != leg_id:
            continue
        current = active.get(identifier)
        if role.get("status") == "accepted":
            if current is None:
                errors.append("role %s accepted without effective acceptance" % identifier)
            elif current["artifact"] != role.get("artifact"):
                errors.append("role %s current artifact has no matching acceptance" % identifier)
            elif latest_review.get((identifier, current["artifact"])) != current["validation_seq"]:
                errors.append("role %s effective acceptance was superseded by a newer validation" % identifier)
            elif current["sha256"] is not None:
                artifact, issue = _local_file(root, current["artifact"], "accepted artifact", "missing accepted artifact")
                errors.extend(issue)
                if artifact is not None:
                    try:
                        digest = hashlib.sha256()
                        with artifact.open("rb") as source:
                            for chunk in iter(lambda: source.read(65536), b""):
                                digest.update(chunk)
                        actual = digest.hexdigest()
                    except OSError:
                        errors.append("role %s accepted artifact could not be read" % identifier)
                    else:
                        if actual != current["sha256"]:
                            errors.append("role %s accepted artifact SHA256 differs from journal" % identifier)
        elif current is not None:
            errors.append("role %s is incomplete or otherwise inactive but has an active acceptance" % identifier)
    return errors


def _anchor_errors(root, evidence, label):
    errors = ["%s: %s" % (label, error) for error in validate_evidence(evidence)]
    if isinstance(evidence, dict) and evidence.get("kind") == "file" and _filled(evidence.get("path")):
        path, issue = _local_file(root, evidence["path"], "evidence file", "missing evidence file")
        errors.extend(issue)
        lines = evidence.get("lines")
        if path is not None and isinstance(lines, list) and len(lines) == 2 and all(
            isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in lines
        ):
            try:
                with path.open("rb") as source:
                    line_count = sum(1 for _ in source)
                if lines[1] > line_count:
                    errors.append("%s: evidence line range exceeds file line count" % label)
            except OSError:
                errors.append("%s: evidence file could not be read" % label)
    return errors


def _nonblank_list(value, label):
    if not isinstance(value, list) or any(not _filled(item) for item in value):
        return ["%s must be a list of nonblank strings" % label]
    return []


def _decision_dependency_errors(root, synthesis):
    """Check stated decision conditions, without claiming their sources are true."""
    selected = synthesis.get("selected_approach_id")
    dependencies = synthesis.get("decision_dependencies", [])
    if not isinstance(dependencies, list):
        return ["synthesis.decision_dependencies must be a list"]
    errors = []
    if selected is not None and not dependencies:
        errors.append("synthesis selected approach requires a decision dependency")
    for index, dependency in enumerate(dependencies):
        label = "synthesis.decision_dependencies[%d]" % index
        if not isinstance(dependency, dict):
            errors.append("%s must be an object" % label)
            continue
        if not _filled(dependency.get("condition")):
            errors.append("%s.condition is required" % label)
        required = dependency.get("required_for_outcome")
        if not isinstance(required, bool):
            errors.append("%s.required_for_outcome must be a boolean" % label)
        status = dependency.get("status")
        if not isinstance(status, str) or status not in VALID_DEPENDENCY_STATUSES:
            errors.append("%s.status must be supported, unverified, or contradicted" % label)
        evidence = dependency.get("evidence")
        if not isinstance(evidence, list):
            errors.append("%s.evidence must be a list" % label)
        else:
            for anchor_index, anchor in enumerate(evidence):
                errors.extend(_anchor_errors(root, anchor, "%s.evidence[%d]" % (label, anchor_index)))
            if status == "supported" and not evidence:
                errors.append("%s supported condition requires evidence" % label)
        if required is True and isinstance(status, str) and status in {"unverified", "contradicted"}:
            if not _filled(dependency.get("verification_step")):
                errors.append("%s.verification_step is required for unresolved required condition" % label)
            if selected is not None:
                errors.append("synthesis selected approach has unresolved required decision dependency")
    return errors


def _digest_errors(root, role, digest, roles, approaches):
    """Validate one current digest and the prerequisites named by it."""
    leg_id = role.get("leg_id", "<unknown>")
    kind = role.get("role")
    errors = []
    for key in ("leg_id", "role", "host", "model", "effort", "artifact"):
        if digest.get(key) != role.get(key):
            errors.append("artifact %s %s does not match role" % (leg_id, key))
    revision = digest.get("revision")
    if type(revision) is not int or revision < 1:
        errors.append("%s %s revision must be a positive integer" % (kind, leg_id))
    predecessor = digest.get("supersedes")
    if "supersedes" not in digest or (predecessor is not None and not _filled(predecessor)):
        errors.append("%s %s supersedes must be null or a predecessor path" % (kind, leg_id))
    elif predecessor is None:
        if type(revision) is int and revision > 1:
            errors.append("%s %s supersedes is required after revision 1" % (kind, leg_id))
    else:
        prior_path, issue = _local_file(root, predecessor, "supersedes", "missing supersedes")
        errors.extend(issue)
        current_path, _ = _local_file(root, role.get("artifact"), "artifact", "missing artifact")
        if prior_path is not None and prior_path == current_path:
            errors.append("%s %s supersedes cannot be current artifact" % (kind, leg_id))
        if type(revision) is int and revision == 1:
            errors.append("%s %s revision 1 must not supersede" % (kind, leg_id))
        if prior_path is not None and prior_path != current_path:
            prior, read_errors = _read_json(prior_path, "supersedes %s" % predecessor)
            # A malformed format-correction original may not parse. Check only readable metadata.
            if not read_errors:
                for key in ("leg_id", "role", "approach_id", "author_leg_id", "target_id"):
                    if key in prior and key in digest and prior[key] != digest[key]:
                        errors.append("%s %s supersedes %s conflicts" % (kind, leg_id, key))
                prior_revision = prior.get("revision")
                if type(prior_revision) is int and type(revision) is int and prior_revision >= revision:
                    errors.append("%s %s supersedes revision must be lower" % (kind, leg_id))

    if kind == "gather":
        if not _filled(digest.get("lens")):
            errors.append("gather %s lens is required" % leg_id)
        errors.extend(_nonblank_list(digest.get("gaps"), "gather %s gaps" % leg_id))
        findings = digest.get("findings")
        finding_ids = set()
        if not isinstance(findings, list):
            errors.append("gather %s findings must be a list" % leg_id)
        else:
            for index, finding in enumerate(findings):
                label = "gather %s finding %d" % (leg_id, index)
                if not isinstance(finding, dict):
                    errors.append("%s must be an object" % label)
                    continue
                identifier = finding.get("finding_id")
                if not _filled(identifier):
                    errors.append("%s finding_id is required" % label)
                elif identifier in finding_ids:
                    errors.append("%s duplicate finding_id: %s" % (label, identifier))
                else:
                    finding_ids.add(identifier)
                if not _filled(finding.get("source_fact")):
                    errors.append("%s source_fact is required" % label)
                for legacy in ("claim", "basis"):
                    if legacy in finding:
                        errors.append("%s legacy %s is forbidden" % (label, legacy))
                errors.extend(_anchor_errors(root, finding.get("evidence"), label))
        inferences = digest.get("inferences")
        if not isinstance(inferences, list):
            errors.append("gather %s inferences must be a list" % leg_id)
        else:
            for index, inference in enumerate(inferences):
                label = "gather %s inference %d" % (leg_id, index)
                if not isinstance(inference, dict):
                    errors.append("%s must be an object" % label)
                    continue
                if not _filled(inference.get("claim")):
                    errors.append("%s claim is required" % label)
                if "evidence" in inference:
                    errors.append("%s direct evidence is forbidden" % label)
                premise_ids = inference.get("premise_ids")
                if not isinstance(premise_ids, list) or not premise_ids:
                    errors.append("%s premise_ids must be a nonempty list" % label)
                    continue
                seen_premises = set()
                for premise in premise_ids:
                    if not _filled(premise):
                        errors.append("%s premise_ids must contain nonblank finding IDs" % label)
                    elif premise in seen_premises:
                        errors.append("%s duplicate premise_id: %s" % (label, premise))
                    else:
                        seen_premises.add(premise)
                        if premise not in finding_ids:
                            errors.append("%s unresolved premise_id: %s" % (label, premise))
    if kind == "draft":
        if digest.get("author_leg_id") != leg_id:
            errors.append("draft %s author_leg_id does not match role" % leg_id)
        for key in ("title", "central_assumption", "proposal", "rough_effort", "falsifying_test"):
            if not _filled(digest.get(key)):
                errors.append("draft %s %s is required" % (leg_id, key))
        for key in ("dependencies", "risks"):
            errors.extend(_nonblank_list(digest.get(key), "draft %s %s" % (leg_id, key)))
        evidence = digest.get("evidence")
        if not isinstance(evidence, list):
            errors.append("draft %s evidence must be a list" % leg_id)
        else:
            for index, anchor in enumerate(evidence):
                errors.extend(_anchor_errors(root, anchor, "draft %s evidence %d" % (leg_id, index)))
        identifier = digest.get("approach_id")
        linked = [a for a in approaches if isinstance(a, dict) and _filled(identifier) and a.get("approach_id") == identifier]
        if not linked:
            errors.append("draft %s approach_id has no approach" % leg_id)
        elif len(linked) > 1:
            errors.append("duplicate approach_id: %s" % identifier)
        elif linked[0].get("author_leg_id") != leg_id:
            errors.append("draft %s does not match approach author" % leg_id)
    if kind == "judge":
        for key in ("reason", "consequence"):
            if not _filled(digest.get(key)):
                errors.append("judge %s %s is required" % (leg_id, key))
        for key in ("keep_clauses", "unknowns"):
            errors.extend(_nonblank_list(digest.get(key), "judge %s %s" % (leg_id, key)))
        if not isinstance(digest.get("severity"), str) or digest["severity"] not in VALID_SEVERITIES:
            errors.append("judge %s severity must be none, minor, major, or critical" % leg_id)
        if not isinstance(digest.get("required_revision"), str) or (
            digest.get("verdict") == "revise" and not _filled(digest.get("required_revision"))
        ):
            errors.append("judge %s required_revision must be a string, actionable for revise" % leg_id)
        counterevidence = digest.get("counterevidence")
        if not isinstance(counterevidence, list):
            errors.append("judge %s counterevidence must be a list" % leg_id)
        else:
            for index, item in enumerate(counterevidence):
                label = "judge %s counterevidence %d" % (leg_id, index)
                if not isinstance(item, dict):
                    errors.append("%s must be an object" % label)
                    continue
                if not _filled(item.get("source_fact")):
                    errors.append("%s source_fact is required" % label)
                if not _filled(item.get("bearing_on_target")):
                    errors.append("%s bearing_on_target is required" % label)
                if "claim" in item:
                    errors.append("%s legacy claim is forbidden" % label)
                errors.extend(_anchor_errors(root, item.get("evidence"), label))
        if digest.get("judge_leg_id") != leg_id:
            errors.append("judge %s judge_leg_id does not match role" % leg_id)
        if not isinstance(digest.get("verdict"), str) or digest["verdict"] not in VALID_VERDICTS:
            errors.append("judge %s verdict must be keep, revise, or kill" % leg_id)
        target = digest.get("target_id")
        linked = [a for a in approaches if isinstance(a, dict) and _filled(target) and a.get("approach_id") == target]
        if not linked:
            errors.append("judge %s target_id has no approach" % leg_id)
        elif len(linked) > 1:
            errors.append("duplicate approach_id: %s" % target)
        else:
            author_id = linked[0].get("author_leg_id")
            author_rows = [r for r in roles if isinstance(r, dict) and _filled(author_id) and r.get("leg_id") == author_id]
            if len(author_rows) != 1:
                errors.append("approach %s author_leg_id must identify one draft role" % target)
                if len(author_rows) > 1:
                    errors.append("duplicate leg_id: %s" % author_id)
            else:
                author = author_rows[0]
                errors.extend(validate_role_map({"roles": [author]}))
                if author.get("role") != "draft":
                    errors.append("approach %s author must be a draft role" % target)
                if author_id in (leg_id, digest.get("judge_leg_id")):
                    errors.append("author cannot judge own approach: %s" % target)
                if author.get("status") != "accepted":
                    errors.append("judge %s target draft must be accepted" % leg_id)
                if author.get("role") == "draft":
                    author_path, issue = _local_file(root, author.get("artifact"), "target draft artifact", "missing target draft artifact")
                    errors.extend(issue)
                    if author_path is not None:
                        author_digest, issue = _read_json(author_path, "target draft %s" % author_id)
                        errors.extend(issue)
                        if author_digest is not None:
                            errors.extend(_digest_errors(root, author, author_digest, roles, approaches))
                            if author_digest.get("approach_id") != target or author_digest.get("author_leg_id") != author_id:
                                errors.append("approach %s does not match author draft" % target)
                            if digest.get("target_artifact") != author.get("artifact"):
                                errors.append("judge %s target_artifact does not match current draft" % leg_id)
                            if type(digest.get("target_revision")) is not int or digest.get("target_revision") != author_digest.get("revision"):
                                errors.append("judge %s target_revision does not match current draft" % leg_id)
        target_path, issue = _local_file(root, digest.get("target_artifact"), "target_artifact", "missing target_artifact")
        errors.extend(issue)
        if type(digest.get("target_revision")) is not int or digest.get("target_revision", 0) < 1:
            errors.append("judge %s target_revision must be a positive integer" % leg_id)
    return errors


def _duplicate_gather_lens_errors(root, roles, focus_leg_id=None, include_incomplete=False):
    """Reject repeated current gather lens names without requiring future digests."""
    seen = {}
    errors = []
    for role in roles:
        if not isinstance(role, dict) or role.get("role") != "gather":
            continue
        leg_id = role.get("leg_id")
        if not _filled(leg_id):
            continue
        status = role.get("status")
        if status != "accepted" and not (
            status == "incomplete" and (include_incomplete or leg_id == focus_leg_id)
        ):
            continue
        artifact, issue = _local_file(root, role.get("artifact"), "artifact", "missing artifact")
        if issue:
            continue
        digest, issue = _read_json(artifact, "artifact %s" % leg_id)
        if issue or not _filled(digest.get("lens")):
            continue
        if (digest.get("role") != "gather" or digest.get("leg_id") != leg_id
                or digest.get("artifact") != role.get("artifact")):
            continue
        lens = " ".join(digest["lens"].split()).casefold()
        first_leg = seen.get(lens)
        if first_leg is not None and (focus_leg_id is None or focus_leg_id in (first_leg, leg_id)):
            errors.append("duplicate gather lens: %s repeats %s" % (leg_id, first_leg))
        else:
            seen.setdefault(lens, leg_id)
    return errors


def validate_campaign(root: Path):
    """Check a campaign's links, digest shapes, and local artifacts."""
    root = Path(root)
    campaign_path = root / "campaign.json"
    if not campaign_path.is_file():
        return ["missing campaign.json"]
    campaign, errors = _read_json(campaign_path, "campaign.json")
    if errors:
        return errors
    errors = []
    if not _filled(campaign.get("campaign_id")):
        errors.append("campaign.campaign_id is required")
    if not _filled(campaign.get("status")) or campaign["status"] not in VALID_CAMPAIGN_STATUSES:
        errors.append("campaign.status must be design_pending or solo_analysis")
    if "approaches" not in campaign or not isinstance(campaign["approaches"], list):
        errors.append("campaign.approaches must be a list")
    if "synthesis" not in campaign or not isinstance(campaign["synthesis"], dict):
        errors.append("campaign.synthesis must be an object")
    if not _filled(campaign.get("ledger")):
        errors.append("campaign.ledger is required")
    errors.extend(validate_role_map(campaign))
    if "events" in campaign:
        errors.extend(validate_events(root, campaign))
    roles = campaign.get("roles", [])
    if not isinstance(roles, list):
        return errors
    if not roles:
        errors.append("campaign.roles must not be empty")
    errors.extend(_duplicate_gather_lens_errors(root, roles, include_incomplete=True))
    role_by_id = {r["leg_id"]: r for r in roles if isinstance(r, dict) and _filled(r.get("leg_id"))}
    solo_analysis = campaign.get("status") == "solo_analysis"
    if solo_analysis:
        for role in roles:
            if isinstance(role, dict) and role.get("role") == "judge":
                errors.append("solo_analysis cannot include judge role: %s" % role.get("leg_id", "<unknown>"))
    if solo_analysis and any(isinstance(role, dict) and role.get("role") == "judge" and role.get("status") == "accepted" for role in roles):
        errors.append("solo_analysis cannot claim accepted judge review")
    approaches = campaign.get("approaches", [])
    if not isinstance(approaches, list):
        approaches = []
    approach_by_id = {}
    for i, approach in enumerate(approaches):
        if not isinstance(approach, dict) or not _filled(approach.get("approach_id")):
            errors.append("approaches[%d].approach_id is required" % i)
            continue
        identifier = approach["approach_id"]
        if identifier in approach_by_id:
            errors.append("duplicate approach_id: %s" % identifier)
        approach_by_id[identifier] = approach
        author_leg_id = approach.get("author_leg_id")
        if not _filled(author_leg_id) or author_leg_id not in role_by_id:
            errors.append("approach %s author_leg_id has no role" % identifier)
        elif role_by_id[author_leg_id].get("role") != "draft":
            errors.append("approach %s author must be a draft role" % identifier)
    ledger = campaign.get("ledger")
    if ledger is not None:
        _, issue = _local_file(root, ledger, "ledger", "missing ledger")
        errors.extend(issue)
    synthesis = campaign.get("synthesis")
    if isinstance(synthesis, dict):
        errors.extend(_decision_dependency_errors(root, synthesis))
        accepted = synthesis.get("accepted_leg_ids", [])
        if not isinstance(accepted, list):
            errors.append("synthesis.accepted_leg_ids must be a list")
        else:
            for leg_id in accepted:
                if not _filled(leg_id):
                    errors.append("synthesis.accepted_leg_ids must contain leg IDs")
                    continue
                row = role_by_id.get(leg_id)
                if row is None:
                    errors.append("synthesis accepted leg has no role: %s" % leg_id)
                elif row.get("status") != "accepted":
                    errors.append("synthesis cites incomplete or unaccepted leg: %s" % leg_id)
        selected = synthesis.get("selected_approach_id")
        if selected is not None:
            if not _filled(selected):
                errors.append("synthesis.selected_approach_id must be an approach ID or null")
            elif selected not in approach_by_id:
                errors.append("synthesis selected_approach_id has no approach")
    judged_approaches = set()
    for role in roles:
        if not isinstance(role, dict):
            continue
        leg_id = role.get("leg_id", "<unknown>")
        artifact, issue = _local_file(root, role.get("artifact"), "artifact", "missing artifact")
        if issue:
            if role.get("role") == "judge":
                errors.append("judge %s incomplete: %s" % (leg_id, "; ".join(issue)))
            else:
                errors.extend(issue)
            continue
        digest, issue = _read_json(artifact, "artifact %s" % leg_id)
        errors.extend(issue)
        if issue:
            continue
        digest_errors = _digest_errors(root, role, digest, roles, approaches)
        errors.extend(digest_errors)
        if (role.get("role") == "judge" and role.get("status") == "accepted"
                and not digest_errors and _filled(digest.get("target_id"))):
            judged_approaches.add(digest["target_id"])
    for approach_id in approach_by_id:
        author_id = approach_by_id[approach_id].get("author_leg_id")
        author = role_by_id.get(author_id) if _filled(author_id) else None
        if author is not None and author.get("role") == "draft":
            author_path, issue = _local_file(root, author.get("artifact"), "author draft artifact", "missing author draft artifact")
            if author_path is not None:
                author_digest, issue = _read_json(author_path, "author draft %s" % author_id)
                if author_digest is not None and (
                    author_digest.get("approach_id") != approach_id
                    or author_digest.get("author_leg_id") != author_id
                    or author_digest.get("artifact") != author.get("artifact")
                ):
                    errors.append("approach %s does not match author draft" % approach_id)
        if not solo_analysis and approach_id not in judged_approaches:
            errors.append("approach %s incomplete: no accepted independent judge artifact" % approach_id)
    return errors


def validate_leg(root: Path, leg_id: str):
    """Check one existing role, its digest, and links needed by that digest."""
    root = Path(root)
    campaign_path = root / "campaign.json"
    if not campaign_path.is_file():
        return ["missing campaign.json"]
    campaign, errors = _read_json(campaign_path, "campaign.json")
    if errors:
        return errors
    roles = campaign.get("roles")
    if not isinstance(roles, list):
        return ["campaign.roles must be a list"]
    matches = [role for role in roles if isinstance(role, dict) and role.get("leg_id") == leg_id]
    if not matches:
        return ["unknown leg: %s" % leg_id]
    if len(matches) > 1:
        return ["duplicate leg_id: %s" % leg_id]
    role = matches[0]
    if campaign.get("status") == "solo_analysis" and role.get("role") == "judge":
        return ["solo_analysis cannot include judge role: %s" % leg_id]
    errors = validate_role_map({"roles": [role]})
    if "events" in campaign:
        errors.extend(validate_events(root, campaign, leg_id=leg_id))
    if errors:
        return errors
    artifact, issue = _local_file(root, role["artifact"], "artifact", "missing artifact")
    if issue:
        return issue
    digest, issue = _read_json(artifact, "artifact %s" % leg_id)
    if issue:
        return issue
    approaches = campaign.get("approaches")
    if not isinstance(approaches, list):
        errors.append("campaign.approaches must be a list")
        approaches = []
    errors.extend(_digest_errors(root, role, digest, roles, approaches))
    if role.get("role") == "gather":
        errors.extend(_duplicate_gather_lens_errors(root, roles, focus_leg_id=leg_id))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Campaign directory")
    selected = parser.add_mutually_exclusive_group()
    selected.add_argument("--leg", help="Check one leg's structure and journal status")
    selected.add_argument("--events", action="store_true", help="Check journal, current roles, and present gather lenses without requiring future digests")
    args = parser.parse_args(argv)
    if args.events:
        campaign_path = args.root / "campaign.json"
        if not campaign_path.is_file():
            errors = ["missing campaign.json"]
        else:
            campaign, errors = _read_json(campaign_path, "campaign.json")
            if not errors:
                errors = validate_role_map(campaign) + validate_events(args.root, campaign)
                if isinstance(campaign.get("roles"), list):
                    errors.extend(_duplicate_gather_lens_errors(args.root, campaign["roles"]))
    else:
        errors = validate_leg(args.root, args.leg) if args.leg is not None else validate_campaign(args.root)
    for error in errors:
        print("ERROR: " + error)
    if args.leg is not None:
        print("Leg %s: structure only for the selected digest; journal status checked when opted in; other planned digests are unchecked." % args.leg)
    if args.events:
        print("Events: journal, current role status, and present gather lens names only; future planned digests are unchecked.")
    campaign_path = args.root / "campaign.json"
    if campaign_path.is_file():
        campaign, parse_errors = _read_json(campaign_path, "campaign.json")
        if not parse_errors and campaign.get("status") == "solo_analysis":
            print("solo_analysis: Independent agents and judges did not run.")
        if not parse_errors and "events" in campaign:
            print(EVENT_LIMITS)
    elif args.events:
        print(EVENT_LIMITS)
    print(LIMITS)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
