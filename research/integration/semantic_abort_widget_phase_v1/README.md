# Cancellation capability depends on widget and effect phase

**Issue #3936 — PASS_WIDGET_PHASE_BOUNDARY_SCOPED.** Successor to closed #771, contributing a live-widget boundary to open #2197. This is not completion of #2197's same-model, held-out application acceptance or of the global roadmap.

## H / T / D / C / U

**H:** Physical button neutrality and semantic cancellation are different facts. Moving outside before release can suppress a release-triggered Button command, but cannot undo an application effect that a Scale has already produced on press. A current widget-scoped capability gate should refuse the unsupported route before input.

**T:** Exactly one formal invocation, allocation `widget-phase-3936-formal01`: 2 widget classes x 5 recipes x 3 repetitions = 30 fresh application processes. Native XTEST events operate unmodified ttk.Button and Tk Scale class bindings. Ordinary application callbacks append effect journals; the controller cannot invoke callbacks or set post-ready values. Separate X-server observer connections record actual button/key state. Each row retains raw IPC, application events, effects, widget identities/geometry/bindings, timestamps, process exits and cleanup. Order is repetition, button/scale, then the five recipes in the table below.

**D:** All 30 rows, exact source/process/event accounting and the preregistered effect gates pass. Independent raw-only audit: 30/30, no integrity errors or gate failures. Six corruption controls reject after their manifests are recomputed. Formal reruns, replacements and post-freeze tuning: zero.

**C:** Provided Linux x86_64 execution container, CPython 3.13.5, Tcl/Tk 8.6.16; 64 installed executable/library/source hashes retained. Docker CLI was absent: no Docker/OrbStack replication or pinned-image claim. An allocation-owned Xvfb used TCP-disabled transport and ephemeral authentication; only its own processes were cleaned up. No provider/model call, shared desktop input, production runtime/CLI mutation, or network use in the experiment.

**U:** Finite hand-scoped toolkit fixture only. Unknowns include acquiring trustworthy current capabilities in real applications, transferring across toolkits, interpreting uncertain effects with a model, and end-to-end usefulness/cost. This does not certify arbitrary cancellation recipes, general GUI reliability, crash-safe cleanup, latency/token savings or human-tempo benefit.

## First formal result

Each cell below has three fresh sessions. Effect counts mean sessions with actual callback-written application effects, not predicted effects. Zero presses for a refused route is pre-input prevention, not successful cancellation of an active operation.

| Recipe | Button effect sessions | Button task presses | Scale effect sessions | Scale task presses |
| --- | ---: | ---: | ---: | ---: |
| COMPLETE | 3/3 | 3 | 3/3 | 3 |
| RELEASE_ONLY_CANCEL | 3/3 | 3 | 3/3 | 3 |
| MOVE_AWAY_CANCEL | 0/3 | 3 | 3/3 | 3 |
| CAPABILITY_GATED_CANCEL | 0/3 | 3 | 0/3 | 0 |
| STALE_CAPABILITY_CANCEL | 0/3 | 0 | 0/3 | 0 |

All **30/30 final server button and key states were empty**, and all application exits were zero. Scale effects were already present at the post-press observation in **9/9 admitted Scale sessions** and independently preceded release in the application journal. All Button post-press observations had zero effects; inside release produced its ordinary callback, while moving away first suppressed it in this fixture.

The current gate is deliberately limited to this Button and recipe. It rejects Scale (3/3) and deliberately stale epoch receipts for both widgets (6/6) before any task press. The stale controls are constructed metadata, not naturally occurring races.

## Integration handoff

This resolves a concrete result/recovery contract boundary, not a complete desktop integration. A downstream integration must keep physical release evidence separate from application-effect disposition. A neutral endpoint cannot by itself justify `SEMANTIC_ABORTED`: report a committed effect, verified absence of effect, or unknown effect as distinct outcomes. Require a current target/recipe/phase-compatible capability before promising cancellation without effect. A recipe verified on another widget is insufficient. Once input is active, unsupported cancellation must not suppress mandatory release; its semantic outcome still needs separate observation.

The next acceptance work belongs to #2197: expose verified capabilities and uncertain/committed effects to the same model on a held-out real application route, independently score decisions/effects/releases, and account for model calls/tokens and task outcome. This bundle neither performs nor substitutes for that experiment. #57 and global ROADMAP.md also remain open.

## Preserved construction failures

`construction-01` stopped before input because Xauthority was unavailable; cleanup then consumed the unread ready response and the app was killed. Its raw records and exact source are retained. Construction was repaired with allocation-owned authentication and ready-first IPC.

`construction-02` completed four sessions with neutral cleanup, but the Scale effect gate failed: bounding-box center was not the trough. Its raw records and source are retained. Before formal freeze, the read-only `coords(75)` target was required to identify `trough2`; no controller callback or post-ready value-setting was introduced.

`construction-03` passed all four excluded live cases and raw audit. Six evidence-corruption controls and pure admission controls passed before freeze. A separate preformal package-metadata `PackageNotFoundError` is retained; installed python-Xlib source hashes are used rather than inventing a distribution version. No construction row is pooled into the 30 formal rows.

## Reproduce the audit without running the experiment

From this directory, with Python's standard library only:

```sh
python unpack.py retained
python retained/audit.py retained/formal01
python retained/controls.py retained/formal01
```

`unpack.py` verifies all four part hashes, the compressed/decoded hashes, exact member hashes and the 195-file denominator before writing a new directory. It refuses replacement and does not execute experimental code. The auditor imports neither controller nor application. Controls alter missing/duplicate cases, a boolean epoch, release state, effect value and process status, then recompute the manifest; rejection is not merely caused by a stale digest.

The retained bundle includes the complete formal evidence, all construction failures and source revisions, environment, plan, preformal freeze, audit, controls and post-run source check. Readable top-level fixture/controller/auditor/control files are identical to the frozen copies in the bundle. The top-level runner alone is not a portable launch command: its full source/environment prerequisites are inside the retained snapshot. **Do not rerun the consumed allocation.** A live replication requires a separate Issue, allocation, output and environment freeze.

## Provenance and delivery

Intake main: `b2457b746a6df06f6536585dfe2ab937aff639f4`. README, docs/CURRENT_GOAL.md, ROADMAP.md, open/closed Issues, open PRs and branches were inspected through GitHub MCP. The duplicate #493 allocation was excluded after checking its retained PR #479 lineage. Historical #706/#771/PR #2214 evidence is unchanged. Only `research/integration/semantic_abort_widget_phase_v1/` is added; branch `research/semantic-abort-widget-phase-20260922` owns publication.

Preformal freeze was posted to #3936 before any formal row, on 2026-09-21 UTC / 2026-09-22 JST. Exact consumed command:

```text
python run.py --mode formal --out formal01 > formal01.stdout.json 2> formal01.stderr.txt
```

| Artifact | SHA-256 |
| --- | --- |
| FREEZE.json | `64c2e9ed9bfa0f1c2a8c802974159b702f7093f2362252755406d2244751d262` |
| formal01/MANIFEST.json | `b24cf5bfdabce9eabf5d95ad161302c71b524fa96bc20b35116f43e83df93312` |
| formal01.audit.json | `7b2fb9abe090d99ca7629b7a7d2e7d8c5fb002bf75fd1ffcb8e29f04859176c2` |
| formal01.controls.json | `497b137f296e917cbdfa0c37fad4b755ea35035530a748f9e1018ec088ca0c68` |
| Compressed evidence | `7880e4070abf2d7663e679047c3d648cf20d427d3b8bfe271718358d8ad53ffb` |
| Decoded evidence, 576339 bytes / 195 files | `2693bcc89ba483f6ece7e2f1771a6b250c228b11d7c98cacda928b2adb14b279` |

The decoded bundle re-audits identically to the original formal audit. At publication commit `fb97e4ebc1e73e6d33ea4dfc4b4c32e169a89168`, all eleven code/freeze/envelope/part Git object IDs were read back through MCP and match locally computed Git blob IDs. This README is a postformal report, not a change to the frozen source or decision gates. The bounded experimental roadmap is complete through raw audit; PR merge/readback and branch lifecycle are recorded separately on #3936. No repository-wide test-suite or integrated-product PASS is claimed by the local study.
