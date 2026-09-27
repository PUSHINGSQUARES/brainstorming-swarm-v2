# Codex Host Guide

## Host Observation

| Field | Observation |
| --- | --- |
| Host | Codex desktop app, exact app version unverified |
| Runtime engine | Native session metadata reported `0.158.0-alpha.2` on 2026-09-27. This is not the desktop app version. |
| Separate CLIs observed | The package-manager CLI on `PATH` reported `codex-cli 0.154.0`; a separate user-local CLI reported `codex-cli 0.156.1` on 2026-09-26. Neither identifies the live desktop app. |
| Model identity | Native turn contexts reported `gpt-6-sol` at `high` effort for one operator and two children on 2026-09-27. |
| Probe date | 2026-09-27, bounded local synthetic campaign |
| Support status | `candidate` until exact app version, clean-launch provenance, lifecycle evidence, and a sanitized public receipt complete the support gates |
| Live host version | unverified |
| Live model ID | `gpt-6-sol`, observed in native turn contexts |
| Live probe date | 2026-09-27 |
| Live receipt | none |
| Authentication and billing | Desktop session authentication observed through callable tools; billing terms unknown. No extra API key was requested for the listed collaboration tools. |
| Spawn, wait, and cancel | Native calls were exercised in a local synthetic probe. A public receipt for the exact host tuple is pending. Automatic termination at a deadline remains unverified. |

The local synthetic run was independently audited, but its launch prompt is encrypted in the available host record and the exact desktop app version is unknown. These partial observations do not qualify the exact host tuple as `tested`. Record a dated, independently reviewed public receipt before changing the status.

## Installation And First Run

Copy the entire `brainstorming-swarm-v2` directory into a Codex skill location configured for your installation. Keep `SKILL.md`, `references/`, and `templates/` together. Reload skill discovery if needed, then ask Codex to use Brainstorming Swarm V2 on the invented library example in the [README](../../README.md#first-run).

The exact skill location and reload procedure for this desktop version are unverified. If no skill loader is available, open [SKILL.md](../../SKILL.md) and its linked method as references. That manual path does not add agent tools or permissions.

## Native Collaboration Inventory

The current Codex session exposes these callable tools. Their availability does not assert identical behavior on other versions.

| Operation | Exposed native surface | Current evidence and limit |
| --- | --- | --- |
| Spawn | `collaboration.spawn_agent({task_name, message, fork_turns?, model?, reasoning_effort?})` | The tool accepts a plain-text task. Up to four concurrency slots are documented for this session, including the parent. Treat a spawn response as a start claim until completion and output are inspected. |
| Wait | `collaboration.wait_agent({timeout_ms?})` | Waits for mailbox updates. It has no per-child target selector; inspect the delivered message or final result before accepting an artifact. |
| Follow up | `collaboration.followup_task({target, message})` | Sends a new task and triggers a turn if the child is idle. |
| Message | `collaboration.send_message({target, message})` | Delivers a message without starting an idle child's turn. |
| Cancel current turn | `collaboration.interrupt_agent({target})` | Requests an interruption of the child's current turn. Check its returned status and later state before claiming termination. |
| Inspect agents | `collaboration.list_agents({path_prefix?})` | Scope `path_prefix` to this campaign's child names. An unscoped listing can disclose unrelated agent results. It does not establish completed artifact quality. |

The interface delivers child messages and final answers to the parent. Use the campaign ledger to record each leg's requested role, actual output, status, and evidence. Check files or other claimed artifacts directly before acceptance. Treat a child's final text as a claim until its referenced material is inspected.

## Model, Effort, And Isolation

- **Model selection:** `spawn_agent` accepts an optional `model` override. The available model list shown to this session includes Codex models, but that list does not prove the current model identity or a successful override. Omit the field to inherit the parent's model.
- **Effort selection:** `spawn_agent` accepts `reasoning_effort` when the chosen model supports it. The tool requires `fork_turns` set to `none` or a positive integer string when an override is explicitly required. Omit both overrides for the session default. Verify an explicit requirement with a live probe before assigning that leg.
- **Context fork:** `fork_turns` accepts `all`, `none`, or a positive integer string. The default inherits the surrounding turns. This controls conversation context, not filesystem isolation.
- **Filesystem isolation:** No worktree or separate filesystem parameter appears on `collaboration.spawn_agent`. Agents share the current directory and filesystem. Assign disjoint file ownership for parallel writes, and use a separate, verified isolation mechanism if the campaign requires it. Do not call shared-directory execution isolated.

### Required Route Preflight On Codex Desktop

The following adapter has been observed with the local Codex desktop JSONL format. It is a host-specific route check, not a portable API or proof of the provider's backend. If the environment variable or record format is absent in your host version, keep required availability `unknown` and stop the task leg.

1. Leave the planned role rows `incomplete` with required model and effort availability `unknown`. Record the desktop app version from the installed application's bundle metadata if available. A CLI engine version is a separate value.
2. Spawn one bounded **calibration child** before sending any campaign evidence. Set `fork_turns: "none"` and pass the exact required `model` and `reasoning_effort`. Its only job is to return the fixed token `ROUTE_OK` and its own `CODEX_THREAD_ID` environment value, obtained with `python3 -c 'import os; print(os.environ.get("CODEX_THREAD_ID", ""))'`. It must not read files, probe private paths, use the network, or spawn children. Wait for a completed result; a spawn response alone is insufficient.
3. From the public package root, run `python3 scripts/check_codex_route.py <child-thread-id> <exact-model-id> <exact-effort>`. The checker validates the UUID, searches only rollout filenames for that exact ID under the current user's default Codex sessions directory, and evaluates only session identity and turn contexts in the matching rollout. It prints no message bodies or account data. If this installation stores sessions elsewhere, provide its known directory with `--session-root`; do not broaden the search to unrelated user records. The helper requires host support for safe descriptor-relative, no-follow file opens and fails closed when unavailable. Record its exit status, observed pair, evidence reference, and time in the ledger's Required Route Preflight table. If it fails, do not relabel availability to satisfy the campaign checker.
4. Only after the calibration completes and the scoped host record matches both required settings, mark matching planned rows `available` and start task-bearing children. A new host version or invocation mode needs a new calibration. For each task child, compare its own scoped native record when available before accepting the artifact. The calibration does not prove another child's settings.

This is a local empirical adapter. `CODEX_THREAD_ID` was exposed to a child shell on the observed desktop, and its local `turn_context` reported model and effort. Other Codex versions or operating systems may store records differently. Never fall back to an unscoped agent listing, a child self-description, or a guessed model ID. A successful local record check is host-reported configuration, not independent attestation of actual backend compute.

## Cancellation And Artifact Collection

Set a bounded deadline for each leg. A local probe crossed its predeclared cutoff while the child remained active; the deadline did not terminate the child automatically. On timeout, call `interrupt_agent` for each active child, inspect the returned status, and use a campaign-scoped `list_agents({path_prefix})` query or a later mailbox update to confirm that work stopped. Until confirmed, record `termination_unknown` and avoid accepting late results.

Collect the child's returned text and any referenced files after the wait barrier. Validate the gather, draft, or judge shape against the package templates. Open cited files and check decisive evidence anchors. The Codex tool inventory does not promise automatic campaign storage, immutable receipts, or independent citation verification.

## Unsupported Or Unverified Operations

- Partial local observations exist, but a public receipt and exact desktop app version remain unavailable, so this route is still `candidate`.
- Automatic termination at a deadline and clean-launch prompt provenance remain unverified.
- `spawn_agent` exposes no native campaign scheduler, dependency barrier, artifact store, or worktree isolation option.
- A model catalogue, CLI installation, or app feature outside this session does not establish that the same operation works in every Codex host.
- This guide does not assert a CLI subagent command, an authentication flag, or a billing rate. Use the observed desktop collaboration API for this candidate route.

If independent spawn fails in the live host, use the skill's `solo_analysis` path and disclose that no independent review ran.
