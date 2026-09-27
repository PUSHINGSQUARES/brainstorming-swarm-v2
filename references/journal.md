# Event Journal

New campaigns create an empty `events.ndjson` beside `campaign.json` and set `"events": "events.ndjson"` in the manifest. The journal is the acceptance history. `LEDGER.md` is a mutable summary that links its events. Older campaigns without an `events` field keep their original ledger method; do not silently recast their history as a native journal.

Write one UTF-8 JSON object per physical line, ending each line with a newline. Append at the end only. `seq` starts at `1` and equals the physical line number. `at` is a UTC time such as `2026-09-27T01:19:00Z`, with optional fractional seconds. Times must be nondecreasing, but they are operator supplied; a checker cannot certify when an event happened. Do not backdate. Keep old lines even when they contain mistakes.

## Validation Before Acceptance

1. Keep the role `incomplete`. Run `python3 scripts/check_campaign.py path/to/campaign --leg g1` if Python is available. Inspect every decisive `source_fact` against its one cited anchor. Check gather premise IDs and judge bearings where relevant.
2. Compute the exact submitted artifact's SHA-256 with a host tool. Append a `validation` object with `seq`, `at`, `type`, `leg_id`, `artifact`, `sha256`, `result` (`pass` or `fail`), `checker`, `source_review`, and `status_during_event: "incomplete"`. `source_review` names the actual factual clauses and anchors inspected. The checker requires at least 20 characters and a colon; a generic “reviewed” fails and would not document the judgment anyway.
3. Only after a passing validation, update the role's manifest status to `accepted`. Append an `acceptance` object with `seq`, `at`, `type`, `leg_id`, `artifact`, `sha256`, and `validation_seq` pointing to that earlier passing validation. Its artifact and hash must match. If the write fails, restore the role to `incomplete` and stop.
4. Run `python3 scripts/check_campaign.py path/to/campaign --events` when Python is available. This checks journal order and current statuses without demanding future digests. Reopen the file and confirm the new line is last when checking manually. Start dependent work only after the acceptance record exists and the available check passes.

The checker requires `sha256` as 64 lowercase hexadecimal characters. If the host has no SHA-256 tool, use `sha256: null` and the same nonempty `hash_limit` explanation in both validation and acceptance. Say explicitly that **artifact tampering cannot be checked**; a claim such as “tamper-proof” is false. Never invent a hash. The artifact path names the exact immutable revision relative to the campaign.

These are **field shapes**, not ready-to-use evidence. Replace every placeholder with a real value and a real hash before appending:

```json
{"seq":1,"at":"2026-09-27T01:19:00Z","type":"validation","leg_id":"g1","artifact":"digests/g1.r1.json","sha256":"<64 lowercase hex of g1.r1.json>","result":"pass","checker":"--leg g1 exit 0","source_review":"f1: sources/brief.md lines 3 to 4 support the full source fact; inference premise f1 resolves","status_during_event":"incomplete"}
{"seq":2,"at":"2026-09-27T01:20:00Z","type":"acceptance","leg_id":"g1","artifact":"digests/g1.r1.json","sha256":"<same 64 lowercase hex>","validation_seq":1}
```

## Corrections And Revocation

An incorrect journal event stays in place. Append a `correction` with `seq`, `at`, `type: "correction"`, `corrects_seq`, `reason`, and `effect`: `annotation`, `retract`, or `barrier_unproven`. An annotation preserves effective state. Retraction and `barrier_unproven` invalidate the targeted validation or acceptance. A correction cannot make an acceptance valid if its required validation was absent or later in the journal. If dependent work already used that acceptance, record the breach, revalidate the current revision, and repeat affected review. Do not rewrite the earlier lines or label the repaired record as proof of the original barrier.

A parseable validation with an invalid value in a recognized field may be retracted **before any acceptance refers to it**. This covers a blank checker or a mistyped hash, not missing or unknown fields. Append the retraction, then a fresh valid validation and acceptance. The faulty line stays visible. A later failed validation for the same artifact closes an earlier pass. If that artifact was already accepted, revoke its acceptance, set the role `incomplete`, and record a fresh passing validation and acceptance. An older pass does not become usable again merely because it is still in the journal.

To withdraw an active acceptance, append a `revocation` with `seq`, `at`, `type: "revocation"`, `leg_id`, `acceptance_seq`, and `reason`. Set the role `incomplete`. A later acceptance requires a fresh passing validation recorded after the revocation. A changed or corrected digest uses a new artifact revision and its own validation and acceptance pair. Preserve superseded digest links and unfavorable verdicts in the ledger.

If an append fails or a line has malformed JSON, a blank line, missing or unknown fields, a sequence/time-order defect, or an unsafe or missing artifact path, stop dependent work. Those historical defects cannot be made valid by a later correction; preserve the failed journal and start a linked fresh campaign if work must continue. The checker also rejects missing or reversed validation, wrong revision or hash, and an accepted role without effective acceptance. It does not prove source truth, that earlier lines were never rewritten, native agent timing, or human approval. An independent native audit or external checkpoint is needed for those claims.
