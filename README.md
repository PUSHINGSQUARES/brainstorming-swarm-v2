# Brainstorming Swarm V2

A portable skill for turning an open question into a reviewed design choice. It uses native agent tools for independent discovery, competing approaches, and critique, then stops for a human decision.

The written method can also guide `solo_analysis` when independent agents are unavailable. That outcome carries an explicit label and does not claim independent review.

## Install

Copy this entire directory into your host's native skill location as `brainstorming-swarm-v2`. Keep `SKILL.md`, `references/`, and `templates/` together so relative links resolve. Use the matching host guide for its verified installation and invocation steps. Reload skill discovery if that host requires it.

If your host has no skill loader, open [SKILL.md](SKILL.md) as a reference and provide its linked files to the agent. Reading the method alone does not grant spawn, network, or filesystem permissions.

## First Run

Ask your agent:

> Use Brainstorming Swarm V2 to compare wayfinding options for an invented civic library. The building has two floors and a narrow entrance wall. Consider visitor accessibility, staff maintenance, and cost. Use only these supplied facts, label assumptions, and stop for my design decision. Use independent agents if available; otherwise label the result solo_analysis.

Follow the [quick path](SKILL.md), keep a campaign directory for the artifacts, and review the [full method](references/method.md) for evidence and lifecycle rules. The [scope](templates/scope.md) and [ledger](templates/ledger.md) provide the starting records. Start an empty `events.ndjson` file beside `campaign.json`; follow the [event journal guide](references/journal.md) to append validation and acceptance records as work proceeds.

If the question includes local source files and the approved privacy and write boundaries permit a copy, copy only the allowed files unchanged into a `sources/` folder inside the campaign before assigning agents. Record their origins and the allowed read boundary in the scope. This gives file evidence anchors stable paths relative to the campaign. Otherwise, keep the files at their allowed locations and use an appropriate URL or registered supplied-context anchor. Do not invent a file path or duplicate excluded material.

## Host Guides

- [Claude](references/host-guides/claude.md)
- [Codex](references/host-guides/codex.md)
- [Grok](references/host-guides/grok.md)
- [Muse](references/host-guides/muse.md)

Read [SUPPORT.md](SUPPORT.md) for the current exact host/model matrix and proof links. `tested` means a dated live probe for the stated tuple; `candidate` means it remains unproven; `unavailable` means the required route could not run. Installation or a model listing does not prove support. A changed host version or model identity, or a probe older than 90 days, requires a new probe before retaining `tested`.

## Optional Checker

The written method runs without Python. If you want local structural checks, use Python's standard library and the included [checker](scripts/check_campaign.py):

```sh
python3 scripts/check_campaign.py path/to/campaign
```

Copy [role-map.json](templates/role-map.json) to `campaign.json` in your campaign directory. Fill its roles, approach records, synthesis, ledger link, and event-journal link as the run proceeds. Create each linked digest from its template. Template examples illustrate fields; they are not evidence of a completed run. Preplanned `incomplete` rows point to future artifacts. Run the checker at a completed stage or campaign barrier; it exits nonzero until all retained linked artifacts exist. Interim missing-artifact errors describe unfinished work, not a green campaign.

For a solo run, set `campaign.status` to `solo_analysis`, remove unused planned agent rows, and keep only actual gather and draft outputs by the current agent. Register each draft through its `approach_id` and `author_leg_id`; put self-critique in the draft or ledger, with no judge rows. State that all outputs share one agent identity. The checker accepts that explicit solo structure, but a pass never means a completed swarm or independent review. See the [routing method](references/method.md#route) for exact availability and solo rules.

Before accepting each submitted leg, run `python3 scripts/check_campaign.py path/to/campaign --leg g1` with that leg's ID. It checks the named digest without requiring future planned outputs. Check each `source_fact` against its one cited source. Gather `inferences` cite the IDs of all factual premises; judge `bearing_on_target` explains the effect on the reviewed draft outside the source fact. If one sentence combines facts from different sources, split it into separate findings or judge items first. Append the passing validation to `events.ndjson` while the leg is `incomplete`; then mark the role `accepted`, append its matching acceptance event, and run `python3 scripts/check_campaign.py path/to/campaign --events` before dependent work. A malformed or unsupported leg stays `incomplete` until a new revision passes. At the end, run the full campaign check shown above.

The checker validates structure, links, local artifact presence, and recorded event order. It cannot prove a journal was never rewritten, a citation is true, an author is independent, reasoning quality, concurrency, cancellation, or freshness. It makes no model or network calls and requires no third-party packages.

## Boundaries

The package supplies a method, templates, and native-host guides. It does not supply a universal scheduler or require a paid provider. Any external processing needs authorization for its cost and privacy boundary. Design approval precedes PRD writing; review of the written PRD precedes task planning. Execution and publication are separate decisions.

## License

[MIT](LICENSE).
