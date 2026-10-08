# Issue #4130 — synchronized task-key release telemetry boundary

## Disposition

**PASS_KEY_UP_TELEMETRY_BOUNDARY_SCOPED** on one prospectively source-frozen 24-cell private Xvfb/XTEST allocation. Formal retries/replacements/post-freeze source edits: 0.

The experiment validates one measurement boundary only: after a task-key `KeyRelease` XTEST operation and XSync return, an owner/program/step/key-bound `key_released` receipt can expose an acknowledged up endpoint without changing the directed input/cancel behavior in this fixture.

It does **not** establish physical HID timing, MAP01 occupancy, useful control, model/task benefit, production runtime semantics, or cross-platform behavior.

## H/T/D/C/U

- **H** — a receipt emitted only after key-up sync can replace the ordinary-hold upper endpoint based on later verified-empty cleanup with an owner-synchronized up endpoint while preserving cancellation and neutral release.
- **T** — BASELINE vs KEY_UP_RECEIPT; ORDINARY_SINGLE, ORDINARY_MULTI, CANCEL_AFTER_HELD, CANCEL_DURING_ADMISSION; 3 repetitions = 24 fresh sessions. Private TCP-disabled Xvfb, Python-Xlib/XTEST, no model/game/network experiment.
- **D** — all 24 worker exits zero; all actual X event press/release cardinalities match admitted keys; every candidate receipt corresponds exactly to an admitted key and precedes independently queried verified-empty release; no receipt is minted for the unadmitted second key in directed partial admission; all terminal keymaps neutral; raw auditor errors=[]; 10/10 corruption challenges rejected.
- **C** — X server logical state is not physical-device telemetry. Directed barriers choose cancellation placement. Multi-key input is sequential. Same-author separate auditor is not independent human review.
- **U** — exact effect on #443 v38/v39 interval width remains unknown until this telemetry exists in a separately frozen compatible trace; usefulness/survival/reaction benefit remains unmeasured.

## Matrix result

Candidate release receipt counts per repetition:

| schedule | admitted keys | candidate `key_released` receipts | full keyset established |
|---|---:|---:|---|
| ORDINARY_SINGLE | 1 | 1 | yes |
| ORDINARY_MULTI | 2 | 2 | yes |
| CANCEL_AFTER_HELD | 2 | 2 | yes |
| CANCEL_DURING_ADMISSION | 1 of 2 | 1 | no |

BASELINE emits no per-key release receipt while performing the same directed XTEST press/release schedule and reaching the same neutral endpoint.

Across the 12 candidate cells there are 18 release receipts total, exactly one per actually admitted key. No baseline cell contains a release receipt.

## Diagnostic timing only

These are descriptive owner-clock intervals, not a latency benchmark:

| schedule | acknowledged first-down → acknowledged last-up median | last up ACK → verified-empty median |
|---|---:|---:|
| ORDINARY_SINGLE | 220.507 ms | 0.082 ms |
| ORDINARY_MULTI | 220.781 ms | 0.137 ms |
| CANCEL_AFTER_HELD | 35.619 ms | 0.114 ms |
| CANCEL_DURING_ADMISSION | 0.110 ms | 0.054 ms |

One ORDINARY_MULTI candidate repetition took 275.073 ms for the 220 ms requested sleep; it is retained and not excluded. CPU scheduling is uncontrolled and timing is not a decision gate.

## Retained construction failure

Construction-01 stopped before input because Python-Xlib required a missing `/opt/xvfb/.Xauthority` despite a private `-ac` Xvfb. That STOP_SETUP was recorded in Issue #4130. Construction correction set `XAUTHORITY=/dev/null` for the private TCP-disabled Xvfb only. Construction-04 passed 8/8 excluded cells and 10/10 controls before public freeze.

## Freeze / provenance

- intake main: `5337efa0394d2c0e4a6d5cb8010f177caf042681`
- public freeze head: `739fe47b3a2b3455c2e3b90a061cd08d01548a0b`
- FREEZE SHA-256: `0bc09c81c20054d4ee9af17d57561f75afe568cd98100794e570c5fe8befc385`
- formal `rows.json` SHA-256: `2f7ce5ad2a76f2db3a0d448952639b28e88b6e250b812a471efb0c3404762c47`
- formal `EXECUTION.json` SHA-256: `d1f315584f542bdc86218f9d578cbf76e27b1b82390efa288a81e477d9a55fc1`
- raw audit SHA-256: `97f0959bac75757011c816bf395192715de6a9ac682fbc7c0322a7b62c36f9a8`
- summary RESULT SHA-256: `da4c21187f2c2129a30d5ba96695c17a46d5df3fe9395605eb8177492e7a63b7`

Actual environment: supplied Linux 6.18.44 x86_64 execution container, CPython 3.13.5, Python-Xlib 0.15, private Xvfb. No Docker/OrbStack image identity.

## Integration handoff

This result supports adding an explicitly non-authoritative release timestamp field to a future instrumentation-only InputOwner successor. It does not authorize modifying the current MAP01 controller in this PR. The next legal scientific question is whether the same receipt, once present in a compatible retained/live trace, reduces #443 occupancy censoring below the predeclared bound without changing release/cancel behavior. A new MAP01/model allocation is not justified by this fixture alone.
