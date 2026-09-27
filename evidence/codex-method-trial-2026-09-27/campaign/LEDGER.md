# Campaign Ledger

## Scope

- Campaign ID: `cedar-wayfinding-firstuse-r2`
- Scope: [SCOPE.md](SCOPE.md).
- Outcome: A human design decision on offline wayfinding to a shaded, step-free drinking-water refill point within the £8,000 pilot cap.
- Execution mode: Six recorded Codex child legs across discovery, proposal, and critique. The operator recorded two dispatches before either result arrived at each stage; simultaneous backend compute was not observed. Exact child identifiers remain private.
- Boundary: Human design approval. No PRD, task plan, or implementation.
- Allowed task sources: Four unchanged copies under `sources/`. No network or external models used.

## Exact Quotes

| ID | Quote | Source |
| --- | --- | --- |
| q1 | "Visitors need to find a shaded drinking-water refill point and a step-free route to it without relying on a smartphone." | `sources/brief.md:3` |
| q2 | "The pilot must cost at most £8,000." | `sources/brief.md:7` |
| q3 | "Management approval has not been granted for any design." | `sources/operations-note.md:6` |

## Supplied Context Registry

- No supplied-context IDs. Source files copied unchanged from the four-file packet before dispatch; all digest anchors point to these campaign copies.

## Native Capability Observations

| Capability | Observation | Evidence reference |
| --- | --- | --- |
| Host and version | Codex desktop native collaboration was callable. Exact desktop app version not exposed. | Live `collaboration.spawn_agent` responses in this session |
| Spawn and result | The operator recorded six child returns and their completion messages. Exact host-returned references remain private. | Public aliases below; native records retained privately |
| Model and effort | Both unspecified; `session-default` was passed by omission. No scoped runtime model or effort metadata was exposed, so actual identities remain unknown. | Native spawn schema and responses |
| Concurrency | Two children were launched before either completion at each stage. The host did not expose compute-overlap timestamps; no exact concurrency claim. | Dispatch order and wait completions |
| Isolation and artifacts | Shared filesystem; disjoint digest paths assigned. Each claimed output was opened and validated. | `digests/`, events 1-21 |
| Cancellation | Not exercised; automatic deadline termination unverified. | No cancellation event |
| Authentication and billing | Native tools were callable. No billing or backend identity evidence surfaced. | Spawn responses only |

### Public Child Aliases

| Leg | Public alias |
| --- | --- |
| g1 | `child-g1` |
| g2 | `child-g2` |
| d1 | `child-d1` |
| d2 | `child-d2` |
| j1 | `child-j1` |
| j2 | `child-j2` |

- These aliases identify the ledger legs only. They are not native host receipts. The exact native names and their mapping to these aliases remain in the private trial record.

## Required Route Preflight

- No explicit model or effort was required. The public method therefore used labelled session defaults and no synthetic calibration child. Spawn and completed output demonstrated default-route availability, not actual model identity.

## Digest Index

| Leg | Role | Current revision | Status | Preserved earlier revision |
| --- | --- | --- | --- | --- |
| g1 | Visitor/access discovery | [g1.r2.json](digests/g1.r2.json) | accepted, events 6-7 | [g1.r1.json](digests/g1.r1.json), accepted 1-2, revoked 3 for unsupported shade inference |
| g2 | Operations/cost discovery | [g2.r1.json](digests/g2.r1.json) | accepted, events 4-5 | none |
| d1 | Physical sign trail a1 | [d1.r1.json](digests/d1.r1.json) | accepted, events 8-9 | none |
| d2 | Paper guide a2 | [d2.r2.json](digests/d2.r2.json) | accepted, events 18-19 | [d2.r1.json](digests/d2.r1.json), accepted 10-11, revoked 17 for material revision |
| j1 | Independent critique of a1 | [j1.r1.json](digests/j1.r1.json) | accepted, events 12-13 | none |
| j2 | Independent critique of a2 | [j2.r2.json](digests/j2.r2.json) | accepted, events 20-21 | [j2.r1.json](digests/j2.r1.json), accepted 14-15, revoked 16 when target changed |

## Evidence Acceptance And Lifecycle

- Authoritative journal: [events.ndjson](events.ndjson), 21 append-ordered events.
- Each current digest was checked with `--leg`, manually reviewed against its cited original source lines, then validated while `incomplete`, accepted, and checked with `--events` before dependent work.
- g1 correction: Its first inference treated a name as shade evidence. Acceptance was revoked before any draft began; the r2 digest explicitly makes shade unverified. No dependent work used g1.r1.
- a2 revision: j2.r1 found that d2.r1 tested people already given a guide. d2.r2 adds unprompted uptake, retention, later-use, throughput, and paper-handling tests. j2.r2 freshly reviewed that revision. Earlier files and verdict remain linked.
- No deadline, cancellation, failed leg, or late output occurred.

## Decisions

| Decision | Scope and revision | Rationale | Alternatives | Evidence set | Human approval |
| --- | --- | --- | --- | --- | --- |
| Design selection pending; `selected_approach_id: null` | `campaign.json` synthesis | Shade at West Canopy, full cost, sign positions and permission, visitor comprehension, closure handling, hours, and approval remain unresolved. A judge `keep` validates a conditional concept, not these facts. | QR-only map rejected against phone and operations constraints. a2 remains a conditional alternative with additional distribution dependencies. | g1.r2, g2.r1, d1.r1, d2.r2, j1.r1, j2.r2 and original source lines | Pending |

## Dissent

| Source | Issue | Disposition |
| --- | --- | --- |
| j1.r1 | a1 should explicitly count east-fountain misroutes and define same-day closure response. | Retained as validation conditions. |
| j2.r1 | a2 needed unprompted uptake and later-use test. | One bounded material revision made and independently rejudged. Actual outcomes remain unknown. |
| j2.r2 | a2 deployment still depends on shade, route trace, full cost, gate capacity, hours, and approval. | Retained; no design selected. |

## Retrieval Cues

- Cedar Fairground, West Canopy shade unknown, step-free paved route, QR-only hostile instruction, physical sign trail a1, paper guide a2, decision_dependencies, selected_approach_id null.

## Open Questions

| Question | Evidence needed | Blocked stage |
| --- | --- | --- |
| Is West Canopy actually shaded during intended service? | Direct site check at refill point and service times. | Design selection |
| Can a1 signs be placed and understood at every route choice? | Route survey, permission, prototype visitor trial including wheelchair users and east-fountain/lawn misroutes. | Design selection |
| Does either pilot fit the full £8,000 cap? | Complete costed plan including fabrication/printing, placement/distribution, upkeep, and removal. | Design selection |
| What are service hours and same-day closure procedures? | Operations decision and a tested response. | Design selection |
| Is deployment approved? | Recorded management decision. | Deployment |
| Would a2 guides be taken and used without prompting? | Ordinary-gate uptake, retention, later-use, and handling trial. | a2 selection |

## Next Boundary

- Human reviews the conditional test direction in [DESIGN_DECISION.md](DESIGN_DECISION.md). No approach is selected as meeting the brief. Stop at design approval.
