# Public Evidence

This directory contains no live host receipts yet. The [Codex method trial](codex-method-trial-2026-09-27.md) includes a synthetic source packet, campaign artifacts, and a path-rebased independent review report. It is a behavioral example, not a tested-host receipt. The test suite creates other disposable files outside the repository. Those tests exercise validators and never count as support proof.

## Receipt Contract

Store a sanitized JSON receipt here only after a real native-host probe and an independent comparison with its private raw events. Use schema version `1`. The validator rejects unknown fields to reduce accidental transcript disclosure.

The receipt has these fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1`. |
| `host`, `host_version` | Exact observed host and version. |
| `target_model`, `model_id` | Named target and exact runtime model ID. |
| `probe_date` | UTC date `YYYY-MM-DD` on which child legs started. |
| `effort_exposed` | Boolean stating whether the host reports effort. |
| `children` | At least two distinct successful child records. |
| `lifecycle_probes` | Exactly one record each for `missing`, `malformed`, `deadline`, and `cancel`. |

Each child record contains:

- `child_id`: An opaque alias beginning `child-`, followed by lowercase letters, digits, or hyphens.
- `start`, `end`: Timezone-aware ISO timestamps from native events. End must follow start. At least two intervals must satisfy `max(start_a, start_b) < min(end_a, end_b)`; touching endpoints do not overlap.
- `reported_model_id`: The host's runtime observation, matching the receipt's `model_id`.
- `model_source`: Exactly `host`. A requested route or catalogue listing is insufficient.
- `requested_effort`, `reported_effort`: Matching nonempty values when effort is exposed. Both are `null` when the host does not expose effort. Required effort that cannot be verified blocks that route; an unexposed field never proves it was honored.
- `terminal_state`: `completed` for the successful overlap pair.
- `artifact`: An object with `path` and `sha256`. Use a distinct relative path under `evidence/` for each child and the lowercase SHA256 of its bytes. Files must exist; hashes must match. Absolute paths, traversal, and symlink escapes fail.
- `raw_event_ids`: At least two unique opaque aliases, each `evt-` followed by four to 64 lowercase letters or digits. These identify the start and result events in the private mapping. Every event alias must be unique across all child and lifecycle records; one event cannot stand in for another child or probe.

Each lifecycle record contains exactly `kind`, `child_id`, `terminal_state`, and `raw_event_ids`. The event list must contain at least one opaque alias. Allowed terminal states are `completed`, `failed`, `cancelled`, or `termination_unknown`. Only native confirmation permits `cancelled`; an unsupported stop or uncertain outcome uses `termination_unknown`. A missing or malformed artifact does not itself imply that its process is still running or has stopped.

## Sanitization And Review

Keep all native invocation and result events, native child identifiers, mapping tables, account details, and raw transcripts outside this public repository and its Git history. Retain a private mapping from opaque event and child aliases to the originals so an independent reviewer can verify attribution.

Publish only allowed fields and invented probe artifacts. Scrub artifact content before publication. Preserve its native hash privately if sanitization changes its bytes; the public hash checks the published bytes. Independently compare both versions and record that review separately. Do not silently edit proof to make a validator pass.

The structured checker verifies shape, interval arithmetic, exact declared identity matching, local hashes, and lifecycle labels. It cannot authenticate a native event, verify cancellation occurred, detect every private fingerprint, judge the planted flaw, or prove a fresh operator completed the workflow. Separate raw-event, critique, clean-install, and public-scrub reviews must establish those claims.

## Running Checks

From the repository root:

```sh
python3 tests/check_live_receipts.py overlap
python3 tests/check_live_receipts.py model-identity
python3 tests/check_release_matrix.py
python3 -m unittest tests.test_release_matrix_expiry
```

Without explicit arguments, live checks validate the full support matrix, including receipt age and exact host-version/model-ID matching, then select only receipts linked by `tested` rows. Explicit `--receipt` mode checks disposable receipt structure without applying matrix freshness or promotion rules. They fail if none exist. To inspect a disposable fixture, use `--root` with its directory and `--receipt evidence/probe.json`. Repeat `--receipt` to select multiple receipts. Both modes validate the whole receipt contract; the mode labels the requested release check.

Never copy a synthetic test receipt here as public proof. A successful check does not promote a support row automatically.
