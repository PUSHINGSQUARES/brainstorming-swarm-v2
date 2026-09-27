# Grok Host Guide

## Host Observation

| Field | Observation |
| --- | --- |
| Host | Grok Build CLI, observed as `grok 1.0.41 (4220f3b224a6) [stable]` |
| Target model | Grok 4.7 is a candidate target. A bounded live probe selected `grok-4.7` and reported producing model `grok-4.7-build`. |
| Probe date | 2026-09-27, synthetic live probe |
| Support status | `candidate` for Grok 4.7. Native child control and full first use remain unverified. |
| Live host version | `grok 1.0.41 (4220f3b224a6) [stable]` |
| Live model ID | `grok-4.7-build` in stream usage; session selection was `grok-4.7` |
| Live probe date | 2026-09-27 |
| Live receipt | none |
| Authentication and billing | The clean probe used a fresh OAuth login with no API key in the launch environment. The copied stream does not attest to subscription billing class. |
| Install | A clean CLI installation ran the probe. Native skill discovery was not tested. |

The capability inventory below comes from read-only CLI help. The separate live probe confirms two overlapping top-level sessions and their outputs. It does not prove the CLI's native subagent API, cancellation, or a full skill run.

## Bounded Live Observation

Three public synthetic prompts ran once each from a clean probe account and launch context: calibration and two distinct gathering lenses. The two gather turns started within one millisecond, overlapped for 45.203 seconds, and both completed. They were separate top-level sessions launched concurrently, not verified native children of one Grok parent. Both kept a planted instruction inside the source packet as quoted data and withheld design approval. Independent review of retained native records passed this narrow source-boundary observation.

The invocation requested `grok-4.7` and `high`. Native session records selected `grok-4.7`; usage records identify `grok-4.7-build` as the producing model. Session summaries report `high` effort. Retained gather streams do not report effort for each assistant turn, so this probe alone cannot prove per-turn effort delivery. There were no tool calls. Missing output, malformed output, deadline expiry, cancellation, skill discovery, and a full first-use campaign were not tested.

## Installation And First Run

Copy the complete `brainstorming-swarm-v2` directory into a Grok skill location that your installation supports. Keep `SKILL.md`, `references/`, and `templates/` together. The exact location, discovery mechanism, and reload procedure for CLI 1.0.41 remain unverified. If the host does not load this as a skill, open [SKILL.md](../../SKILL.md) and its linked method as reference material. Reading the files does not grant agent or filesystem permissions.

Before a live run, confirm the installed CLI version, active model identity, authentication route, and permission boundary. Ask for the invented library example in the [README](../../README.md#first-run) only after the intended inference and cost boundary is authorized. The bounded probe above used direct prompts; it did not load this package as a skill.

## Native Capability Inventory

| Operation | Observed CLI surface | Evidence limit |
| --- | --- | --- |
| Spawn | `grok --agents <JSON>` accepts inline subagent definitions; `--agent <NAME>` selects an agent name or definition file. `--no-subagents` disables spawning. | Help does not specify the parent-side call that launches a child, a child identifier, or successful execution. Native spawn remains unverified. |
| Wait | `grok dashboard` advertises a view of sessions and subagents; `grok sessions list` lists recent sessions. | Neither help page specifies a child completion barrier or wait operation. Wait remains unverified. |
| Cancel | `grok leader kill` stops all running leader processes. | This is not a documented per-child cancellation command. Child cancellation and confirmed termination remain unverified. Do not use leader kill as a presumed child stop. |
| Model | `--model <MODEL>` appears on `grok` and `grok agent`. | The bounded live sessions selected `grok-4.7` and usage identified `grok-4.7-build`. Child overrides remain unverified. |
| Effort | `--reasoning-effort <EFFORT>` appears on `grok` and `grok agent`. | The bounded live sessions requested `high` and their summaries reported `high`. Per-turn gather effort and child overrides remain unverified. |
| Isolation | `--worktree [<WORKTREE>]` starts a session in a new git worktree; `--worktree-ref <WORKTREE_REF>` chooses its base. `grok worktree` exposes management commands. | Session worktree behavior and child isolation were not run or inspected. A worktree flag does not prove disjoint child filesystems. |
| Artifact collection | `--output-format` lists `plain`, `json`, `streaming-json`, and `streaming-messages-json`; `grok export` advertises Markdown transcript export. | The bounded live probe retained streaming replies and native turn events. Native child attribution, skill artifacts, and full campaign collection remain unverified. Inspect actual files and evidence anchors before acceptance. |

`grok agent` lists `stdio`, `headless`, `serve`, and `leader` modes. Their presence does not establish a swarm scheduler or a parent-side child lifecycle API. The bounded probe used `--prompt-file` and streaming output in separate single-turn sessions.

## Model, Effort, And Campaign Routing

Record the requested target, session-selected model, and producing model identity separately in the role map. The bounded probe observed them, but Grok 4.7 remains a **candidate** until the full support gates and a public receipt pass. When the user specifies a model or effort, stop the affected leg if the host cannot confirm it. For unspecified settings, label them as session defaults instead of inventing a value.

Run distinct discovery, proposal, and critique legs only after verifying independent spawn and a completion barrier in the current host. Keep each leg's output in the campaign ledger. If the native interface cannot launch independent children, follow the skill's `solo_analysis` path. Do not relabel sequential work as parallel.

## Cancellation And Artifact Collection

Set a deadline for each leg before launch. On expiry, stop accepting its output. Request cancellation through a verified child control if one exists, then inspect the child state. Until the host confirms termination, record `termination_unknown`. The observed help inventory provides no verified per-child cancel operation.

Collect each completed gather, draft, or judge artifact after a verified barrier. Check its template shape, inspect every claimed file, and verify decisive evidence anchors. A transcript, final message, or exit claim does not by itself prove that an artifact exists or that independent critique occurred.

## Pending Live Proof

- Confirm native skill discovery for the exact CLI version.
- Confirm billing route and per-turn effort control without exposing credentials.
- Spawn two distinct native children, record host-assigned identities, and prove their execution intervals overlap. The observed top-level sessions do not satisfy this gate.
- Collect separate hashed artifacts and verify their contents and citations.
- Exercise missing output, malformed output, deadline expiry, cancellation request, and confirmed termination.
- Link a sanitized, dated receipt in [SUPPORT.md](../../SUPPORT.md) before changing `candidate` to `tested`.

The bounded live probe did not run a child lifecycle test or a full skill campaign.
