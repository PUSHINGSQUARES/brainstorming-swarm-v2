# Grok Host Guide

## Host Observation

| Field | Observation |
| --- | --- |
| Host | Grok Build CLI, observed as `grok 1.0.41 (4220f3b224a6) [stable]` |
| Target model | Grok 4.7 is a candidate target. Its runtime identity and availability remain unverified. |
| Probe date | 2026-09-26, local help inventory only |
| Support status | `candidate` for Grok 4.7. No live inference or child probe ran. |
| Live host version | unverified |
| Live model ID | unverified |
| Live probe date | unverified |
| Live receipt | none |
| Authentication and billing | The CLI exposes `login` and `--oauth`. The active authentication method, subscription coverage, and billing terms remain unknown. |
| Install | This CLI was present locally. A clean installation and native skill discovery were not tested. |

The observations below come from read-only `grok --version` and help commands. A command shown in help does not prove a successful child run, two-child overlap, actual model identity, or cancellation.

## Installation And First Run

Copy the complete `brainstorming-swarm-v2` directory into a Grok skill location that your installation supports. Keep `SKILL.md`, `references/`, and `templates/` together. The exact location, discovery mechanism, and reload procedure for CLI 1.0.41 remain unverified. If the host does not load this as a skill, open [SKILL.md](../../SKILL.md) and its linked method as reference material. Reading the files does not grant agent or filesystem permissions.

Before a live run, confirm the installed CLI version, active model identity, authentication route, and permission boundary. Ask for the invented library example in the [README](../../README.md#first-run) only after the intended inference and cost boundary is authorized. No live Grok call was made for this guide.

## Native Capability Inventory

| Operation | Observed CLI surface | Evidence limit |
| --- | --- | --- |
| Spawn | `grok --agents <JSON>` accepts inline subagent definitions; `--agent <NAME>` selects an agent name or definition file. `--no-subagents` disables spawning. | Help does not specify the parent-side call that launches a child, a child identifier, or successful execution. Native spawn remains unverified. |
| Wait | `grok dashboard` advertises a view of sessions and subagents; `grok sessions list` lists recent sessions. | Neither help page specifies a child completion barrier or wait operation. Wait remains unverified. |
| Cancel | `grok leader kill` stops all running leader processes. | This is not a documented per-child cancellation command. Child cancellation and confirmed termination remain unverified. Do not use leader kill as a presumed child stop. |
| Model | `--model <MODEL>` appears on `grok` and `grok agent`. | The flag accepts a model ID. Help does not establish the active ID, that Grok 4.7 is available, or that child overrides work. |
| Effort | `--reasoning-effort <EFFORT>` appears on `grok` and `grok agent`. | Help gives no accepted effort values or proof that a requested level reaches a child. |
| Isolation | `--worktree [<WORKTREE>]` starts a session in a new git worktree; `--worktree-ref <WORKTREE_REF>` chooses its base. `grok worktree` exposes management commands. | Session worktree behavior and child isolation were not run or inspected. A worktree flag does not prove disjoint child filesystems. |
| Artifact collection | `--output-format` lists `plain`, `json`, `streaming-json`, and `streaming-messages-json`; `grok export` advertises Markdown transcript export. | Output schemas, child attribution, file persistence, and artifact retrieval remain unverified. Inspect actual files and evidence anchors before acceptance. |

`grok agent` lists `stdio`, `headless`, `serve`, and `leader` modes. Their presence does not establish a swarm scheduler or a parent-side child lifecycle API. The CLI also exposes `--single` and `--prompt-file` for single-turn prompts, but this guide did not execute either.

## Model, Effort, And Campaign Routing

Record the requested target and actual host-reported model identity separately in the role map. Treat Grok 4.7 as **unverified** until a live receipt reports that exact identity. When the user specifies a model or effort, stop the affected leg if the host cannot confirm it. For unspecified settings, label them as session defaults instead of inventing a value.

Run distinct discovery, proposal, and critique legs only after verifying independent spawn and a completion barrier in the current host. Keep each leg's output in the campaign ledger. If the native interface cannot launch independent children, follow the skill's `solo_analysis` path. Do not relabel sequential work as parallel.

## Cancellation And Artifact Collection

Set a deadline for each leg before launch. On expiry, stop accepting its output. Request cancellation through a verified child control if one exists, then inspect the child state. Until the host confirms termination, record `termination_unknown`. The observed help inventory provides no verified per-child cancel operation.

Collect each completed gather, draft, or judge artifact after a verified barrier. Check its template shape, inspect every claimed file, and verify decisive evidence anchors. A transcript, final message, or exit claim does not by itself prove that an artifact exists or that independent critique occurred.

## Pending Live Proof

- Confirm clean installation and skill discovery for the exact CLI version.
- Confirm active authentication, billing route, Grok 4.7 identity, and effort control without exposing credentials.
- Spawn two distinct children, record host-assigned identities, and prove their execution intervals overlap.
- Collect separate hashed artifacts and verify their contents and citations.
- Exercise missing output, malformed output, deadline expiry, cancellation request, and confirmed termination.
- Link a sanitized, dated receipt in [SUPPORT.md](../../SUPPORT.md) before changing `candidate` to `tested`.

No live inference, network request, or child lifecycle test was run while preparing this guide.
