# Claude Host Guide

## Host Observation

| Field | Observation |
| --- | --- |
| Host and version | Local `claude` CLI reports `2.1.215 (Claude Code)` on 2026-09-26. |
| Target model | Opus 5.5 is a candidate target. Its model ID, availability, and runtime identity remain unverified. |
| Probe date | 2026-09-26, local help inventory only. |
| Support status | `candidate`. No inference or child lifecycle probe ran. |
| Live host version | unverified |
| Live model ID | unverified |
| Live probe date | unverified |
| Live receipt | none |
| Authentication and billing | `claude auth` exposes `login`, `logout`, and `status`. The active authentication method, subscription coverage, and billing terms were not inspected. A native authenticated session should use its existing sign-in; this guide does not require a new secret. |
| Install | The CLI was present locally. A clean installation, skill discovery, and invocation were not tested. |

These observations come from `claude --version`, `claude --help`, `claude agents --help`, and `claude auth status --help`. Help text establishes available command syntax, not successful execution or model routing.

## Installation And First Run

Copy the complete `brainstorming-swarm-v2` directory into a Claude Code skill location supported by your installation. Keep `SKILL.md`, `references/`, and `templates/` together. The exact installation path and discovery behavior for CLI 2.1.215 remain unverified. If skill discovery is unavailable, open [SKILL.md](../../SKILL.md) and its linked method as references. Reading the method does not grant agent or filesystem permissions.

Use the invented library example in the [README](../../README.md#first-run) after confirming the current session's inference and cost boundary. Record the active host and model identity in the campaign ledger before assigning any model-specific leg.

## Native Capability Inventory

| Operation | Observed local surface | Evidence limit |
| --- | --- | --- |
| Spawn | `claude --bg` starts the session as a background agent and returns immediately. `claude --agents <json>` defines custom agents, and `claude --agent <agent>` selects one for the current session. | Help does not document a parent-side child launch call, a child identifier, or independent subagent execution. Do not count a background session as a completed discovery leg without a live receipt. |
| Wait | `claude agents --json` prints active sessions as JSON; `--all` also includes completed background sessions. | Help does not document a blocking child completion barrier. Polling semantics, output fields, and completion detection remain unverified. |
| Cancel | No per-child cancellation command appeared in the inspected help. | A timeout or cancellation request cannot be claimed as confirmed termination through this inventory. Record `termination_unknown` until a verified control and state check establish a stop. |
| Model | `claude --model <model>` sets the current session model. `claude agents --model <model>` sets a default for sessions dispatched from agent view. | Help lists aliases such as `opus`, but does not establish an Opus 5.5 ID, availability, or a child override. Record requested and actual identity separately. |
| Effort | `claude --effort <level>` and `claude agents --effort <level>` appear in help. The current-session values are `low`, `medium`, `high`, `xhigh`, and `max`. | No live probe confirmed that a requested level reaches a child. |
| Isolation | `claude --worktree [name]` creates a new git worktree for the session. `--add-dir` permits additional directory access. | Session worktree behavior and child isolation were not tested. Additional directory access is a permission boundary, not isolation. |
| Artifact collection | `claude --print --output-format json` offers a single result; `stream-json` offers realtime output. `claude agents --json --all` lists sessions. | Output schemas, child attribution, file persistence, and transcript access were not inspected. Open each claimed artifact and check evidence anchors before acceptance. |

The CLI also exposes `--resume`, `--continue`, and `--session-id` for session selection. None of those flags proves that a child completed or that its work was independent.

## Model, Effort, And Campaign Routing

Treat Opus 5.5 as **unverified** until a live receipt confirms its exact runtime identity. When a user requires that model or an effort level, stop the affected leg if the host cannot confirm it. For unspecified settings, record `session default` instead of inventing a value.

Before calling this a swarm, verify that the current Claude host can launch two distinct children, identify each one, confirm overlapping execution, and collect separate outputs. The observed CLI help does not provide that proof. If independent spawn is unavailable, follow the skill's `solo_analysis` path and state that independent critique did not run.

## Cancellation And Artifact Collection

Set a bounded deadline before each leg. If the deadline expires, stop accepting that leg's output. Use only a verified stop control for the specific child, then inspect its state. The inspected help does not establish such a control, so record `termination_unknown` until the host proves termination.

After a verified completion barrier, collect each gather, draft, or judge against the package templates. Check cited file lines, supplied context, and URLs directly. A session listing or final message alone does not prove that an artifact exists or that a critique was independent.

## Pending Live Proof

- Confirm skill discovery and invocation on CLI 2.1.215.
- Confirm the active authentication and billing route without exposing credentials.
- Confirm the exact Opus 5.5 model ID and an actual host-reported runtime identity.
- Launch two independent children and prove that their execution intervals overlap.
- Collect separate artifacts and verify their contents and evidence anchors.
- Exercise malformed output, timeout, cancellation, and confirmed termination.
- Link a sanitized, dated receipt in [SUPPORT.md](../../SUPPORT.md) before changing `candidate` to `tested`.

No Claude inference, network request, or child lifecycle test ran while preparing this guide.
