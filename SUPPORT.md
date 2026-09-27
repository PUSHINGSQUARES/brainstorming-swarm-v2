# Host Support

Matrix updated on 2026-09-27. No tuple below has passed every live support gate. Codex and Grok have bounded probes, but neither has a complete public receipt or clean first-use proof. Installed tools and model catalogues alone are inventory, not support evidence.

| Host | Target model | Status | Host version | Model ID | Probe date | Model control | Effort control | Receipt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude | Opus 5.5 | candidate | unverified | unverified | unverified | unverified | unverified | none |
| Codex | GPT-6 Sol | candidate | unverified | gpt-6-sol | 2026-09-27 | observed locally | observed locally | none |
| Grok | Grok 4.7 | candidate | 1.0.41 | grok-4.7-build | 2026-09-27 | model selection observed | session summary high | none |
| Muse | Unverified | candidate | unverified | unverified | unverified | unverified | unverified | none |

Muse is a named target host; its exact runtime model is unverified. No model identity or availability is inferred from that name.

The Grok row records a narrow synthetic probe, not native child support. Two separate top-level sessions overlapped and completed. Their session-selected model was `grok-4.7`; stream usage identified the producing model as `grok-4.7-build`. Session summaries reported `high` effort, while the retained gather streams did not expose effort per assistant turn. A full skill run, failure and cancellation lifecycle outcomes, and independent child control remain unverified.

## Status And Expiry

- **Candidate:** The method targets this tuple, but live evidence is incomplete.
- **Unavailable:** A dated observation found that the exact target could not run. Record the reason in its host guide.
- **Tested:** A real probe and independent audit support this exact host version and model ID. Link its sanitized receipt in the matrix.

A tested row expires when its probe is older than 90 days, its host version changes, or its model ID changes. Day 90 remains current; day 91 does not. Future dates are invalid. Compare the current runtime against the row before use. A change returns the current status to `candidate` until a new probe passes. The checker compares the recorded tuple and receipt; it cannot discover the current installed runtime.

A tested probe needs two distinct overlapping child legs, separate hashed artifacts, host-reported model identity, and matching requested effort when exposed. Lifecycle probes must record missing output, malformed output, deadline expiry, and cancellation. A deadline alone never proves termination.

Independent reviews of native events, seeded critique, hostile-source handling, and clean installation remain release gates. Passing a receipt checker does not satisfy those reviews. An agent-agnostic release claim requires at least two independently tested host families.

## Checks

Run `python3 tests/check_release_matrix.py` to check the matrix. Run `python3 tests/check_live_receipts.py overlap` and `python3 tests/check_live_receipts.py model-identity` to check linked tested receipts. Both live checks fail when no tested receipts exist.

See [receipt format and privacy boundary](evidence/README.md) and the [host guides](references/host-guides/).
