# Campaign Ledger

This is the mutable continuity summary. Keep digests immutable and retain superseded links. The authoritative validation and acceptance order lives in `events.ndjson`, beside `campaign.json`. Repair an event by appending a new event to that file; never rewrite its earlier lines. Bracketed fields are prompts, not evidence.

## Scope

- Campaign ID: [ID]
- Scope record: [Relative link to completed scope]
- Outcome and constraints: [Short statement]
- Execution mode: [Parallel independent agents, serial independent agents, or solo_analysis]
- Current boundary: [Stage and stopping condition]
- Limits: [Budget, deadline, privacy, and read boundary]

## Exact Quotes

| Quote ID | Exact user quote | Context and source |
| --- | --- | --- |
| [ID] | [Verbatim quotation] | [Message or supplied-context reference] |

## Supplied Context Registry

| Stable ID | Bounded source text or allowed source link | Version |
| --- | --- | --- |
| context-1 | [Source text supplied for this campaign] | [Date or revision] |

## Native Capability Observations

| Capability | Observed operation or limitation | Evidence reference |
| --- | --- | --- |
| Host and version | [Observed identity] | [Native event] |
| Spawn and result/wait | [Actual tool or unavailable] | [Native event] |
| Model and effort control | [Required settings and what the host exposes] | [Native event] |
| Concurrency | [Capacity and observed overlap, or serial] | [Native event] |
| Isolation and artifact access | [Read/write boundaries and collection] | [Native event] |
| Cancellation | [Confirmed behavior, unknown, or unsupported] | [Native event] |
| Authentication and billing | [Observed boundary, or unknown] | [Reference without secrets] |

## Required Route Preflight

| Host/interface version and invocation mode | Required model/effort | Synthetic child and result | Host-reported model/effort or unknown | Scoped evidence and verification time | Task rows released or stopped |
| --- | --- | --- | --- | --- | --- |
| [Exact tuple] | [Requested pair] | [Native child ID and fixed-token result, or failure] | [Values from the host record, not a child self-report] | [Reference and time before task dispatch] | [Leg IDs and reason] |

Keep invocation success distinct from runtime settings. A calibration child receives no task evidence. Leave required task rows incomplete and their availability unknown until this record supports them. A prior exact receipt still needs a fresh synthetic readiness call and never proves a new child's runtime identity.

Retain each calibration result, evidence reference, verification time, and released or stopped row set when updating this table. A later route check does not erase the earlier history.

## Digest Index

| Leg ID | Role and lens | Host/model/effort | Revision and artifact | Status | Supersedes and reason |
| --- | --- | --- | --- | --- | --- |
| [ID] | [Role] | [Observed or session-default] | [Immutable digest link] | incomplete | [Earlier link, retained] |

Record each current artifact in `campaign.json`. Keep earlier rows and explain which verdicts a revision invalidates. Preplanned incomplete rows may reference future artifacts; the checker remains nonzero until retained links resolve. Check at stage or campaign barriers and report unfinished work explicitly.

For `solo_analysis`, retain only actual gather and draft records, state that they share the current agent identity, and record self-critique here or in each draft. Do not create judge rows or imply independent review. A structurally valid solo campaign is never a completed swarm.

## Evidence Acceptance And Lifecycle

- Journal: `events.ndjson`
- Last observed event sequence: [Number or none]
- Current accepted revision by leg: [Leg ID, immutable artifact path, and validation and acceptance event sequence]
- Open failed reviews or revoked acceptance: [Leg ID, event sequence, and reason]
- Lifecycle exceptions: [Late output, deadline, cancellation request, confirmed stop, or unknown termination]

This section is a summary of the journal, not a replacement for it. Record source review in a validation event while the role is `incomplete`. Inspect each source fact against its one anchor and check gather premise links or judge bearings. After a passing validation, update the role to `accepted`, append a matching acceptance event, and only then start dependent work. A missing or reversed event is a failed barrier. A later correction cannot move it earlier in history. Keep the old event and the failed state visible; revalidate and repeat affected dependent review if necessary. A late or incomplete artifact stays outside accepted evidence. A stop request alone never means `cancelled`.

## Decisions

| Decision ID | Scope and artifact revision | Decision and rationale | Alternatives rejected | Evidence set | Human approval |
| --- | --- | --- | --- | --- | --- |
| [ID] | [Version] | [Choice or pending] | [IDs and reasons] | [Accepted digest revisions] | [Exact decision reference or pending] |

Record design approval and written-PRD approval separately. Preserve earlier decisions when revising the scope.

## Dissent

| Source leg | Disputed claim or clause | Counterevidence | Disposition and reason |
| --- | --- | --- | --- |
| [ID] | [Claim] | [Anchor] | [Unresolved, accepted, or declined with reason] |

Do not remove dissent because the recommendation prevailed.

## Retrieval Cues

- [Keywords, approach IDs, and question phrases that help the next reader find this work]

## Open Questions

| Question | Why it matters | Owner or evidence needed | Blocks which stage |
| --- | --- | --- | --- |
| [Question] | [Consequence] | [Next check] | [Stage] |

## Next Boundary

[What can proceed, what remains incomplete, and which human decision is pending.]
