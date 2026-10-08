# German AltGr direct-key preflight v2 — retained result

Task `XKB-ALTGR-DIRECT-PREFLIGHT-20260916-002`, Issue #360. Publication BASE `ddc07847f163d0b57fe409f5bc89ca083da1b670`; source-first freeze HEAD `ba5152818c5e06e7fcdabc98a94c0b2579949ed5`.

## Decision

**`RETAIN_ALTGR_DIRECT_PREFLIGHT_SCOPED`.**

The scoped direct-key mechanism safely extends the retained two-level printable-ASCII route to German Group1 level2 through one explicit `Mode_switch`/Mod5 path. It recovers eight previously unrepresentable printable symbols while preserving whole-payload zero-input refusal for the two frozen dead-key-only controls. This is not a generic Unicode, Compose, IME or native-full-XKB result.

## Preregistration chronology

Task #355 was stopped before formal execution because its development construction exceeded that task's own construction allowance. Task #360 explicitly preregistered those excluded observations, permitted no additional development XTEST input before source freeze, and used a new allocation identity. No #355 rows are pooled into this result.

## Formal block

Three fresh `xvfb-run` servers, sixteen fixed payloads per server, 48 first trials total. Every server independently resolved the installed German XKB source to the preregistered SHA-256 `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`.

Frozen payload strata:

- controls: `a`, `A`, `?`;
- historical two-level rejects: `@ [ ] \\ { } | ~ ^` and backtick;
- all-direct mixed payload: `A@[]\\{}|~Z`;
- dead-key refusal payloads: `^`, backtick, `A^Z`, and `A` + backtick + `Z`.

### Outcome

- 36/36 candidate-eligible trials delivered receiver text exactly.
- 12/12 candidate-ineligible/dead-key-containing trials refused before task input with **zero XTEST emissions** and empty receiver text.
- 48/48 trials ended with verified empty physical key/button state.
- 48/48 trials preserved the exact applied keyboard-map hash.
- 48/48 trials preserved the exact modifier-map hash.
- All three fresh servers passed the runner gates and independent audit.

The retained German XKB source reproduces the predecessor's ten two-level missing printable symbols: `@ [ \\ ] ^` backtick `{ | } ~`. Adding direct levels2/3 recovers exactly eight: `@ [ \\ ] { | } ~`. `^` remains `dead_circumflex` on `<TLDE>` and backtick is available only through a dead-grave path (`dead_grave` in the resolved map), so both remain outside this direct-only mechanism.

Across the 36 accepted trials, retained stroke receipts contain 3 level0 strokes, 12 level1 strokes and **48 level2 strokes**; no level3 stroke was required by this frozen payload set. Total XTEST emissions across accepted trials were 246. These counts describe this fixture only and are not latency/performance metrics.

The all-direct mixed payload `A@[]\\{}|~Z` completed exactly 3/3. The mixed negative payloads `A^Z` and `A`+backtick+`Z` refused 3/3 each with no partial prefix delivered, directly exercising whole-payload preflight rather than per-character best effort.

## Independent audit

The frozen auditor imports neither candidate nor projection code. It reparses every retained resolved XKB file, reconstructs direct printable Group1 levels0..3 and keycodes, verifies the historical two-level reject set, checks each accepted stroke against the retained applied core map and modifier map, checks receiver text and exact emission count, verifies rejection side effects are zero, and checks final release/map/modifier invariants.

Result: `PASS_INDEPENDENT_AUDIT`, 48/48.

A separate issue was found **after** formal runner + independent audit completed: the frozen offline corruption helper attempted to `copytree()` the dead `receiver.sock` Unix socket nodes and exited before its first mutation. The formal allocation was not rerun and the frozen helper remains unchanged. A separate posthoc harness, using only retained formal regular-file bytes and the already-frozen independent auditor, excludes the dead socket filesystem nodes and verifies five corruption classes are rejected: wrong receiver text, false emissions on a refusal, keyboard-map mutation, modifier-map mutation and resolved-XKB mutation. This posthoc check is supporting evidence, not a replacement formal gate.

## Evidence boundary

Full conversation archive: `xkb_altgr_direct_preflight_v2_evidence.tar.xz`, 21,384 bytes, SHA-256 `30903fcff884f4fa86ccac235e7899a998e5152c8f72d97b0b38adc8723db76a`; manifest SHA-256 `7e6fe2249c8950e92cf5844782716dc5415634128dd1dd173098de7da708dcdc`; 44 regular files are independently hashed. The three ephemeral formal `receiver.sock` nodes are intentionally excluded and documented; tar also ignores the excluded-construction socket node. The archive contains frozen source, formal regular-file evidence, the original frozen mutation-helper failure, the posthoc mutation harness, and the excluded #355 construction record.

## Limits / next question

Linux 6.18.44, CPython 3.13.5, python-xlib 0.15, Tk 8.6, `setxkbmap` 1.3.4, `xkbcomp` 1.4.7, Xvfb, Intel Xeon Platinum 8370C guest with five visible CPUs. Batch1. No timing claim.

This experiment deliberately projects four resolved XKB symbol levels into a disposable core mapping and uses `Mode_switch` in Mod5. That is a controlled representation of an AltGr-like direct-level route, not proof of native XKB type/group semantics in arbitrary applications. Dead-key composition, Compose, Unicode outside printable ASCII, additional groups, IME, Wayland, physical keyboards, Windows/macOS and natural failure rates remain open.

The next one-variable rung should remove the fixture projection rather than add Compose immediately: test whether a native application path exposes/accepts the same direct level-3 symbols under actual XKB state/types while preserving whole-payload preflight and fail-closed semantics. Dead-key composition should remain a separate later rung.
