# Muse Host Guide

## Host Observation

| Field | Observation |
| --- | --- |
| Host and version | Local `muse --version` reported `Muse Code 1.4.0 (1.4.0-R4161.1)` on 2026-09-26. |
| Target model | Muse is the named host. The exact runtime model identity and availability remain unverified. No model claim is made. |
| Probe date | 2026-09-26, local version and top-level help only. |
| Support status | `candidate`. No inference, child lifecycle, or artifact probe ran. |
| Live host version | unverified |
| Live model ID | unverified |
| Live probe date | unverified |
| Live receipt | none |
| Authentication and billing | Unknown. Help lists `login`, `logout`, and `auth`, but no active route or billing terms were inspected. |
| Install | The CLI was present locally. Clean installation, skill discovery, and invocation remain unverified. |

Both `muse --version` and `muse --help` attempted to write an update-check temporary file beside the CLI. The sandbox denied those writes with `Operation not permitted`, then each command printed the output cited above. The commands did not establish whether an update check completed. No permission escalation or live call followed.

## Installation And First Run

Copy the complete `brainstorming-swarm-v2` directory into a Muse skill location supported by your installation. Keep `SKILL.md`, `references/`, and `templates/` together. The exact location and discovery behavior remain unverified. The CLI lists a `skills` command, but this guide did not inspect or run it. If skill loading is unavailable, open [SKILL.md](../../SKILL.md) and its linked method as references. Reading them grants no agent or filesystem permissions.

Before a live run, confirm the installed version, active model identity, authentication, billing, and permission boundary. Use the invented library example in the [README](../../README.md#first-run) only after authorizing its inference and cost boundary.

## Native Capability Inventory

| Operation | Observed local surface | Evidence limit |
| --- | --- | --- |
| Spawn | Top-level help lists `--agents <JSON>` as one ephemeral agent-definition overlay. | Help does not show a parent-side child launch call, child identifier, or successful independent spawn. |
| Wait | Top-level help lists `resume`, `trace`, and `session-message`. | No child completion barrier or wait operation was observed. Their names do not establish wait semantics. |
| Cancel | No per-child cancellation control appeared in top-level help. | A deadline or cancellation request does not prove termination. Record `termination_unknown` until a verified control and state check establish a stop. |
| Model | `--provider <MODE>` lists `echo` or `meta`, with `meta` as the stated default. `--model <MODEL>` accepts a model ID for non-echo providers. | Help gives no active model ID or runtime identity. Do not infer a model from the host name or default provider. |
| Effort | `--reasoning-effort <EFFORT>` lists `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, and `ultra`, with `high` as the stated default for Meta. | No live probe confirmed that a requested level reaches a child. |
| Isolation | `--worktree` lists session modes `off`, `create`, and `existing`. `--worktree-base` selects a base ref, and `--worktree-existing` names an existing path. `--subagent-worktree-isolation` is described as a compatibility flag. | Help says only an affirmative per-child request asks for isolation, and requests may reject when prerequisites are unavailable. Session and child isolation were not tested. |
| Artifact collection | `export` advertises transcript export, and `trace` advertises session or run trace inspection. `exec` advertises one headless prompt. | Output schema, child attribution, file persistence, and retrieval were not inspected. Open each claimed artifact and check its evidence anchors. |

The top-level help also lists `--parallel-tool-calls`. Parallel tool calls do not prove that two independent agents ran concurrently.

## Model, Effort, And Campaign Routing

Record requested settings and actual host-reported settings separately in the role map. Treat the runtime model as **unverified** until a live receipt identifies it. If a user requires a specific model or effort and the host cannot confirm it, stop that leg. For unspecified settings, record `session default`; the help default alone does not prove a particular run used it.

Before calling this a swarm, verify that Muse can launch two distinct children, identify them, confirm overlapping execution, and collect separate outputs. The observed help does not provide that proof. If independent spawn is unavailable, use the skill's `solo_analysis` path and disclose that independent critique did not run.

## Cancellation And Artifact Collection

Set a bounded deadline before each leg. At expiry, stop accepting its output. Use only a verified stop control for that child, then inspect its state. This help inventory establishes no such control, so record `termination_unknown` until termination is confirmed.

After a verified completion barrier, collect each gather, draft, or judge against the package templates. Inspect the actual files and verify decisive citations. A transcript or final message alone does not prove an artifact exists or that a critique was independent.

## Pending Live Proof

- Confirm clean installation, skill discovery, and invocation on Muse Code 1.4.0.
- Confirm authentication and billing without exposing credentials.
- Record the exact runtime model identity and verify requested effort reaches a child.
- Spawn two distinct children, capture host-assigned identities, and prove overlapping execution.
- Verify a completion barrier, separate artifacts, and their evidence anchors.
- Exercise malformed output, deadline expiry, cancellation, and confirmed termination.
- Link a sanitized, dated receipt in [SUPPORT.md](../../SUPPORT.md) before changing `candidate` to `tested`.

No Muse inference, network request, or child lifecycle test ran while preparing this guide.
