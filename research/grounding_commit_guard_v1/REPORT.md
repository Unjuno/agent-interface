# Grounding commit guard: first retained local GUI matrix

TASK: GROUNDING-COMMIT-GUARD-20260915-01.
BASE: fc38624476aa1f30c381e5932f383224451a7d63.
Pre-execution source/plan freeze: 77c2357ff7fcdc4d44b4fbaa27a317d6d1e9d717.
Disposition: scoped guard mechanics PASS; default promotion FAIL/HOLD.

## Question and relationship to prior work

The earlier grounding_revisit_v1 conversation artifact found that current geometry,
prediction and semantic reacquisition are not sufficient target identity. This is
not a repeat of the concurrently active observation_addressing_v1 grid/AX study.
It isolates the acquisition-to-input boundary. All code is new under this namespace;
existing Executor, workflows, DOOM, native-core and other-agent sources are unchanged.
The baseline is a new current-semantic selector restricted to one named region,
not a claim to execute the old eight-method benchmark verbatim.

## Actual execution

Real Chromium 144.0.7559.96, headful on private Xvfb 1024x768x24. CSS viewport
800x600, DPR 1, measured CSS-to-X11 origin, actual XTest button events and application
trusted-click scoring. Source acquisition is scripted using unique AX button name
Target in region Workspace. Read-only CDP supplies document/backend-node IDs,
AX role/name/disabled state, geometry and topmost-hit information. No LLM, learned
classifier, predictive world model or provider tokens were used.

18 deliberately chosen conditions, three layouts (852101/852102/852103), three
methods, 162 attempts total. Method order rotates across conditions/layouts.
Each method acquires the initial target, receives the same staged transition,
checks current state, receives the next transition, optionally rechecks, receives
the final transition, archives a screenshot and injects a coordinate if proposed.
The final-check arm alone pays another observation. Mutations are staged, not a
continuous-motion experiment or sampled natural failure distribution.

The two explicit boundary-negative cases were nominated before execution:
replacement AFTER the final check, and a business-meaning change in the SAME node
with unchanged AX/geometry. They count in the all-case promotion gate.

## First result: all 54 attempts per method

| Method | Target | Wrong target | Background | No click event | Abstain |
|---|---:|---:|---:|---:|---:|
| Current semantic reacquisition | 9 | 21 | 3 | 3 | 18 |
| Original document/scope/node + early current guard | 9 | 15 | 3 | 3 | 24 |
| Same bound guard + final revalidation | 12 | 6 | 0 | 0 | 36 |

Abstentions are NOT task successes. The candidate's additional target successes
are the three moved-original cases between early and final validation. All three
methods stop on duplicate same-scope labels; another named scope does not confuse
the scoped selector. Binding rejects replacement by a same-name node and scope
replacement before validation. The final check additionally rejects intervening
replacement, rename, overlay and disable transitions.

All three methods fail both boundary-negative cases. Each candidate wrong input
is either post-check replacement or unobservable same-node meaning change. A DOM
node is not a business-object identity, and repeated reads cannot make a later OS
input atomic. A prediction must not be treated as authority for the future state.

The child-span case exposes over-refusal: strict topmost node equality mistakes
a child of the intended button for an unrelated overlay. All methods abstain in
all three layouts. Do not silently replace this with a hit or claim completion.
A descendant-aware repair requires its own negative controls for nested handlers
and separately interactive descendants before another bounded allocation.

## Timing and platform conditions

CPython 3.13.5, Linux 6.18.44 x86_64/glibc2.41, AMD EPYC 9V74 exposed to the
container, affinity CPUs 0-4, sampled 2596.126 MHz (uncontrolled shared-host clock),
NumPy 2.3.5, Pillow 12.3.0, Playwright 1.57.0. These are sequential local cases,
not an inference batch. Full environment snapshots are retained per layout.

Selector-time medians (range), ms: current 5.413 (2.625-9.368); bound early 5.399
(2.277-9.125); bound final 9.602 (5.040-17.875). The extra observation is not free.
These heterogeneous-case medians are diagnostic, NOT a task-speed comparison.

The candidate's last observation to injection gap is median 35.022 ms, range
31.968-48.581 ms. It includes a planned yield and evidence image work. Therefore
final means later in this protocol, NOT atomic or zero-gap input. The two earlier
arms have roughly 58-59 ms median gaps. No hard real-time guarantee is claimed.

## Audit and retention

16 pure selector tests pass. Smoke-01 failed before GUI on missing python-xlib
package metadata despite a usable Xlib module. Smoke-02 changed only environment
reporting to the module version and passed three real/trusted/empty-release clicks.
The smoke seed is excluded. Failed source and complete test transcript are in the
full archive; development/construction.json records the remote index.

All seven source/plan Git blob hashes read back from GitHub match executed local
bytes. The frozen 162-case allocation then completed once, split into three
predeclared layout blocks. Every record was flushed/fsynced; each block was zipped
outside the working result directory before the next block. No same-ID rerun.

There were 84 injected clicks, each with verified empty X11 button state; 78
produced a trusted, coordinate-consistent application event. The other six were
disabled-control no-event outcomes, retained as failures/no effect, not successes.
78 attempts abstained without injection or application event. Release evidence
proves only the measured button state, not correct application meaning.

Offline audit verifies 339 per-layout manifest entries, all 162 row identities,
AX selection replay, point geometry, input/effect coordinates, refusal-without-input
and event ordering. Fresh extraction of the complete ZIP reproduces the audit and
all summary values. All 162 selected repository receipt rows match full raw rows.

Repository retention is deliberately distinguished from conversation retention:
- GitHub: executable source, exact plan, this report, audit summary, every attempt's
  selected receipt fields, construction index and complete-archive identity.
- Full conversation ZIP: all source, full AX trees, geometry, transitions, input
  nanosecond receipts, app effects, 162 trial PNGs, block manifests and smoke records.
  It is NOT uploaded into GitHub/Actions. A GitHub-only clone cannot perform the
  complete raw-data/image replay without this ZIP. Selected fields are not a
  substitute for the full traces.

Archive: agent-interface-commit-guard-evidence.zip, 701515 bytes, 375 entries.
SHA-256: 72a03223f97a8d515b1c1b75e3f8f6da2868a9fa7556a8a6e19562238c89e3b5.
The complete concatenated original raw JSONL is 1620186 bytes, SHA-256
46c97dce132471de42d388911f300760d1163fea39132cda65967ba9761fb83e.

## Reproduction and variable/units contract

Run test_guard.py for deterministic construction. For offline full replay, extract
the exact ZIP and run audit.py with its results directory. Do not rerun the consumed
GUI allocation; a new GUI execution needs a new plan/ID/output directory.

| Field | Meaning | SI / stored unit | Definition and domain | Type |
|---|---|---|---|---|
| document/scope/node | observed identities | dimensionless IDs | positive document-scoped backend IDs; not business identity | integer scalars |
| point | proposed viewport location | CSS px, no physical SI calibration | finite 2-D point inside 800x600, DPR 1 | 2-D vector |
| start_ns/end_ns | observation boundaries | s / ns | ordered same-process monotonic samples | integer scalars |
| last_read_to_injection_us | diagnostic gap | s / microseconds | difference of input start and last read end, rounded | integer scalar |
| selector_median_ms | diagnostic selection cost | s / milliseconds | median of same-clock durations, extra read included | real scalar |

Unit check: differences of monotonic nanosecond samples remain durations; dividing
by 1000 stores microseconds and by 1000000 stores milliseconds. CSS px are not
metres. Browser performance.now is not subtracted from Python monotonic clocks.

## Decision and next task

PASS only for the predeclared, observable pre-final-change guard mechanics.
FAIL/HOLD for universal/default promotion because six wrong candidate inputs remain.
Future work should test document-scoped mutation invalidation plus independently
observable target-effect identity, shorten rather than hide the observation-input
gap, and test descendant-aware hit semantics. None removes the need for ordinary
runtime admission, deadlines, release and independent task-effect checks.

Related disciplines: control systems (feedback vs prediction), accessibility/HCI
(semantic names vs instance identity), and distributed systems (check/use races).
The analogy is explanatory, not evidence of correctness. CDP reference:
https://chromedevtools.github.io/devtools-protocol/1-3/DOM/ .
