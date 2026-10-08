# Click activation: hit target versus keyboard recipient

Allocation: `activation-hit-target-20260922-01`.
Status at this document's freeze: zero formal cases. This is LOCAL preregistration only.
Repository: Unjuno/agent-interface. Intake main: 2308b8301d69b7089a2e0636486736ed59b61537.
Predecessors: closed #55; #4036 / open PR #4053 (head 965cadf1636b00da30ab7044a55c8179c56b5ee6).
Ownership: additive `research/integration/activation_hit_target_v1/` only; proposed/local branch `research/activation-hit-target-20260922`. No remote branch or issue has been created.

## Concrete integration decision

Does an ordinary click used to recover the intended keyboard recipient remain a no-collateral recipe when a different native sibling covers the registered Entry? Separate hit-target evidence before button-down from recipient evidence after release. A successful focus call, unchanged target geometry and eventual neutral input are not task-effect evidence. This is a NEW occlusion/application-support scope explicitly excluded by #4036, not a rerun of its 30 cases. The earlier chat scheduler results remain immutable and are not measurement inputs here.

## H

H1: A registered Entry's native identity and geometry can remain unchanged while an ordinary same-application Button placed above it becomes the native pointer hit target. A geometry-only click followed by typing can invoke that Button and put the digit in the previously focused second Entry.
H2: Checking the intended keyboard recipient after the click prevents that wrong-field text but does not undo the already committed Button callback.
H3: Checking the native pointer hit target before clicking prevents a cover already present at that check, preserving clear and unrelated-overlay positives. A new cover between that check and button-down still permits the collateral callback; a later focus check only refuses the text. The candidate is NOT hypothesized to solve the remaining check/use interval.

This is a finite application/backend characterization of known window-stacking behavior, not a security finding, new X11 theorem, full runtime admission result or general safe recipe.

## T

Environment: provided Linux x86_64 execution container, CPython 3.13.5, Tcl/Tk 8.6.16, installed Python-Xlib (0.15), Xvfb, five allowed guest CPUs. Exact binary/interpreter hashes in ENVIRONMENT.json. No Docker/OrbStack/image attestation, installation, external experiment network, model/provider, host desktop, user document, or clipboard use.

Each batch uses an owned TCP-disabled Xvfb with a private generated MIT cookie; all native effects stay in that server. The authentication cookie is removed at cleanup and is not evidence to publish. Each case launches a fresh Tk application and has a different opaque session ID. Ordinary Entry and Button class bindings are unchanged. Fixture IPC only observes, repositions/maps the cover, or closes; it never inserts task text or directly invokes the callback. Input uses the exact current X11Backend methods. The complete vendored backend Git blob is 9cae101a219348077668c8fc086acf8e13154afe; SHA256 3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8. Loader removes exactly the unused runtime.core_v1.contract import; no method body is rewritten. manifest(), core admission, full execute()/CLI/MCP are not exercised.

Three policies:
- CLICK_THEN_TYPE: common registered-surface focus + pointer move, then click and type the digit.
- POST_FOCUS: same click, but type only with current application-recipient evidence for A.
- HIT_AND_FOCUS: first require the separate X observer's deepest pointer child to be A; then require the same post-click recipient check.

Four schedules: CLEAR; COVER_BEFORE (ordinary cover above A before hit observation); COVER_AFTER (cover only after the hit decision, before click); UNRELATED (same Button elsewhere). Two rotations of policy order yield 24 fresh cases. Two additional NO_TASK_INPUT controls, CLEAR and COVER_BEFORE, retain the common focus/motion but no button or key input. They are NOT zero-OS-input controls. Minimum denominator: 26, not a sample-size estimate.

Use three fixed serial batches of indices 0..8, 9..17, 18..25. Only one invocation per formal batch. Each case has a 12-second application watchdog, bounded 3-second RPC response, 2-second native-event observation deadline, and verified native release. The outer supervisor waits at most 35 seconds per batch and records the real child wait status. No new batch follows a nonzero/missing previous exit or incomplete prior END. Preserve timeout/partial state; no rerun, replacement, pooling with construction, postfreeze tuning, or automatic overlay removal.

Source, independent audit, controls, unit tests, environment, schedule, expected table and construction evidence are hash-frozen locally before formal batch 0. Exact formal commands:
```
python -B launch.py formal <study>/results/formal-batch-00 --batch 0
python -B launch.py formal <study>/results/formal-batch-01 --batch 1
python -B launch.py formal <study>/results/formal-batch-02 --batch 2
```
The runner enforces its own exact source-relative output roots; existing roots refuse. These are recorded reproduction commands, not permission to repeat the retained allocation.

## D

Expected per-policy totals over eight cases:
| Policy | Correct A values | Wrong B values | Cover callbacks |
|---|---:|---:|---:|
| CLICK_THEN_TYPE | 4 | 4 | 4 |
| POST_FOCUS | 4 | 0 | 4 |
| HIT_AND_FOCUS | 4 | 0 | 2 |
The two no-task-input controls remain blank with zero callbacks. Every CLEAR/UNRELATED positive must have A='7', B='', counter=0. HIT_AND_FOCUS refuses both COVER_BEFORE cases before button-down. All COVER_AFTER cases with a click retain the one actual callback, even when the text is refused. These are scope failures for unconditional recovery, NOT safe-candidate successes.

PASS_ACTIVATION_HIT_TARGET_BOUNDARY_SCOPED requires the complete 26-case/3-batch denominator; exact source and process/command/event/effect identity; unchanged target geometry; native and Tk hit-test agreement; exact ordinary input events; independent marker-pixel reconstruction; all release/keymap/button/server/exit gates; zero audit errors; and all 12 frozen copied-evidence mutations rejected. Unit tests require seven successes. Any complete contrary pattern is a hypothesis mismatch; absent/corrupt provenance, process or cleanup evidence is HOLD/STOP. The auditor uses the conservative HOLD_EVIDENCE_OR_GATE_FAILURE envelope for either class and retains exact causes for the report. A boundary PASS does not approve either weak comparator or imply that HIT_AND_FOCUS prevents after-check collateral effects.

## C

A cooperative synthetic app supplies exact Entry identity/geometry and post-click focus. The pointer observer uses a separate native X connection and walks QueryPointer child results; the Tk winfo-containing response is independent cross-checking evidence. Multiple queries and subsequent input are not atomic. There is no popup grab, foreign process overlay, focus change after the post-click check, concurrent geometry edit, disabled field, text selection, IME, window reincarnation, or production semantic target discovery. Two app-observation times are not collapsed into one atomic snapshot claim. The cover's local counter is a harmless private fixture effect, not a user action.

## U

Two directed repetitions are finite coverage, not natural error probability or calibrated reliability. No performance gate, model latency, token reduction, broad correctness, human tempo or runtime promotion. Clock values are diagnostics in the same monotonic domain; X-server millisecond event times are retained but never subtracted from host nanoseconds. CPU frequency/load is uncontrolled. Combined physical measurement uncertainty u_c and coverage factor k are NOT estimated or applicable to this logical contract verdict.

## Variable / field table

| Field | Meaning | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| target / surface / hit / focus | Target, surface, native hit child and Tk recipient identities | 1 | Positive native XID; absent recipient can be null | integer scalar / null |
| geometry | Target root position and extent | 1 (logical pixels, not metres) | x,y integer; width,height positive; frozen 200 by 40 | four-component integer record |
| session | One fresh app lifetime | 1 | Opaque 32-hex identifier supplied to the app | string |
| sequence | Receipt order within one case | 1 | Positive integer | integer scalar |
| captured_ns / decided_ns | Same-container monotonic observation/decision instants | s, stored in ns | nonnegative integer; ordering only, no physical calibration | integer scalar |
| allow | This fixture recipe's next-step eligibility | 1 | true/false, not production authority | Boolean |
| counter | Application Button callback count | 1 | integer initially 0; increments only in ordinary callback | integer scalar |

Unit check: identities, pixel coordinates and event counts are never compared with durations. All temporal order checks compare host nanoseconds within the same domain. No assertion equates X-server logical neutral state with physical hardware state.

## Roadmap and publication

Intake/lineage/collision search -> excluded construction and correction -> exact local source freeze -> three one-shot native batches -> separate raw audit and 12 controls -> lossless evidence, report and additive patch -> GitHub issue/PR/checks/readback when a supported write route exists -> own-branch cleanup only after verified merge/dependency checks.

Current connector discovery exposes 48 read operations and no write action. Plugin search returned the already installed GitHub connector only. Local gh/Docker and GH_TOKEN/GITHUB_TOKEN are absent. This local publication constraint is NOT a global fleet blocker or a new scientific question. Record STOP_PUBLICATION_NO_WRITE_CAPABILITY under this delivery, without inventing a remote Issue/PR number. Public prior results, parallel branches and global ROADMAP remain unchanged.

## Related fields

HCI: click recovery can have effects other than focus. Distributed/concurrent systems: a precheck is not atomic with use. Software verification/metrology: input release, recipient identity and independently observed application effect require separate evidence. These are transfer ideas, not evaluated additional domains.
