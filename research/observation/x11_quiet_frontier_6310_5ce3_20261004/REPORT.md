# #6310 native focus-frontier T1

## First disposition and saved-only qualification

First formal outcome: **STOP_INVALID_NATIVE_EVIDENCE**, audit implementation limitation. Producer ran once, exit0, all15 native rows; frozen auditor ran once, exit1 with ValueError('effective control'). Its copied True→1 coverage mutation changes JSON but Python equality treats it as unchanged. First AUDIT/raw/receipt/frozen source remain intact; no formal/native rerun.

Separate audit_saved_v2.py uses canonical JSON to qualify effective mutations, while retaining the original raw-only reconstruction. Its status is **POSTRUN_SAVED_NATIVE_FOCUS_SUPPORT_SCOPED**, not retrospective formal PASS. Fifteen saved rows reconstruct, all eight effective copied corruptions are refused; a test-first True→1 reproduction failed before the versioned fix. All19 original freeze hashes still match.

| Consumer rule | False A→F quiet labels | Boundary |
| --- | ---: | --- |
| Undrained local journal is empty | 9 | Deliberately stale weak baseline; not an actively polling event loop |
| Native A/F focus values equal | 6 | ABA hidden by endpoint equality |
| Qualified subscription + consumed native event prefix | 0 | Closed-world two-window source only |

Qualified outcomes: six CHANGE_OBSERVED (three ABA, three persistent change), six historical QUIET_AS_OF_FRONTIER (three stable plus three before a later change), three UNKNOWN_NO_COVERAGE (deliberate unsubscribe with real ABA). Three quiet F records subsequently have a source-witnessed change before B. No rule grants input authority. Source records show18 post-A/pre-F FocusOut/In events, six after-F events and60 excluded qualification events. This counts retained focus events, not all setup/cleanup server events or physical input.

## H/T/D/C/U and roadmap disposition

H: a faithful enrolled event stream with an ordered server roundtrip/consumption frontier can distinguish delayed-consumer native focus changes from true quiet for this instrumented predicate. Missing coverage is UNKNOWN, and historical quiet does not close F→B.

T: three repeats × five contexts, each on fresh private Xvfb with two own mapped override-redirect windows, no window manager/user desktop. Three Xlib connections share one producer process (window owner, subscriber, focus mutator). Direct replies on the mutator connection witness every commanded focus state; observer receives genuine native FocusOut/In records and samples A/F. These are independent connections, **not independent observer processes or an authenticated external ground-truth service**. Pre-A four-event ABA qualification plus two IsViewable checks is excluded from scientific endpoints. Formal raw stores every declared mutation/request/reply, subscription declaration/epoch/window IDs, sampled focus, event fields and cleanup.

D: source supports the declared saved-corpus distinction after versioned audit qualification; first formal STOP remains. No new quiescence mechanism is needed: closed #42 already supplies event-generation continuity. Existing mechanism plus explicit prefix/coverage and historical claim typing suffices for this bounded fixture. Broader #6310 stays open.

C: direct fresh focus recheck is a useful stronger baseline but does not detect ABA. A drained generation witness can; this does not show economic superiority over direct rechecks or require a generalized snapshot solver. The stale-journal baseline is intentionally weak; do not present9 as a defect rate of the public runtime.

U: writer completeness is a fixture assumption supported by this frozen closed-world script, not measured arbitrary-desktop enrollment. The local epoch UUID identifies the allocation; it is not a universal immutable-state certificate. No arbitrary app/selection/property/reparent/process-incarnation coverage, missed-subscription detection from silence alone, drop/overflow/load robustness, authenticated timestamps, hard deadline, useful task feedback, key-hold/cancel efficacy, model/token/latency benefit, or production admission is established. The missing-subscription case explicitly declares coverage false; no hidden oracle infers it for the consumer. Focus changes are real SetInputFocus operations, not keyboard/pointer/task emissions. Unknown hidden writers require UNKNOWN outside this fixture.

## Actual source and ordering contract

X11 orders a connection's requests but not unrelated clients. Our host program explicitly waits for each mutator GetInputFocus reply before issuing the observer's later GetInputFocus request; after that response it drains pending native events. The evidence is this serialized source protocol/returned queries plus recorded event witnesses, not mere timestamp closeness or a guess that two clients naturally synchronize. No source mutation is issued between the completed mutator prefix and F. Later post-F mutation is separately witnessed before B.

References: [X.Org core communication](https://www.x.org/guide/communication/) and [X Synchronization protocol ordering limitation](https://xorg.freedesktop.org/releases/X11R7.7/doc/xextproto/sync.html). These describe transport/ordering boundaries, not a general GUI quietness or atomic compare-and-act guarantee. No Beam estimated watermark was used; no distributed-snapshot theorem is claimed.

## Reproduction, failures and resources

Allocation QUIET-X11-6310-T1-5CE3-20261004-01; base a10c6eeff098074862c707d82520d49029ef25e0. Frozen19members in FREEZE.json. Formal raw SHA256286f3db040b8a9f8b4930cc577fd825d20f026428580746f01d20ab611b1054b. Earlier synthetic research/analysis/quiet_frontier_6310_t0_20261002 and closed#42 historical outcomes are unchanged.

Cached image sha256:b2ae049f7c500a3f6b6d162b0351297331434cff5a43f66e1bb41aff90478c96; own OrbStack VM research-59-hud-ocr-5ce3-20261003 ID01M40FX53D7A1NKSVYYKYDARRZ. Stage Engine create/inspect/start/terminal receipts retain actual restrictions. Both formal containers terminal, candidate0/auditor1/noOOM. Python/cgroup measurements: cpu.max100000100000, memory.max536870912, memory.swap.max0, pids.max128 (see ENVIRONMENT for exact strings). Shared hardware and normal-mode VM host mounts mean neither CPU exclusivity nor security isolation is claimed. Xvfb15 exits0; three connections closed and both windows destroyed each cell, focus reset PointerRoot, whole keymap neutral and observed Button1–3 neutral. No all-button/hardware neutrality claim. Ownengine zero-running receipt then exact ownedVM stopped; retained exitedcontainers/image remain recoverable.

Preformal first capture wrapper was invalid because a sparse-excluded predecessor read returned an error that was copied as source. SyntaxError occurred before tests/formal work; construction/first_wrapper_failure.json preserves this incident. No existing file was damaged. Policy tests RED2failures/GREEN6; saved preflight characterization6. Post-run canonical mutation regression RED1failure/GREEN3. Current host16/container16/workspace22/scorer2 tests pass; these are saved/compatibility checks, not new native experiments.

Saved reproduction: python3 -B -m unittest discover -s <this-package> -p 'test_*.py'. Do not invoke consumed run_stage stages or overwrite outputs. audit_saved_v2.py is an exclusive-output saved-only qualifier; inspect existing validation/AUDIT_SAVED_V2.json or direct analyze(raw) for read-only review. Launcher timeout-path cleanup is not promoted as a general watchdog; actual completed stages and final empty engine state are separately evidenced. FILES.json records final hashes excluding itself.

Roadmap next: qualify genuinely complete producers and any F→B conditional check before admission; otherwise historical evidence remains advisory and use ordinary fresh observation/YIELD. Full r134/game/useful-feedback/matched-recovery/model/product goals remain unproven. No other worker's native/application/proposer work was adopted or rewritten.
