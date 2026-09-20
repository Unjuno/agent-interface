# Issue #3796 — full map preflight before formal formula delivery

## H / T / D / C / U

**H** — The two prior setup STOPs were harness defects: an incorrect XLookupString release oracle, followed by an exact-space layout parser. A construction gate that validates both receiver event semantics and the complete US→DE query/server-dump/fresh-map transition will catch such setup defects before formal allocation. Once confirmed, the unchanged backend may deliver `=B2*A2` under the standard German map.

**T** — One allocation, `issue3784-explicit-x11-receiver-formal-03`, under a new additive path. Pin the current-main runtime source closure plus the shared XTEST/XLookupString helper source. First run a separate construction test over one DE-transition server and one non-mutating US control; both receiver controls must pass, DE query must be parsed with variable whitespace, and server dump/fresh core map must change only in DE. Formal runner repeats those same frozen preconditions before any candidate call. If construction fails, retain construction STOP and do not run formal rows. If it passes, run three fresh German Xvfb `-noreset` rows plus one US control; capture baseline/after query, xkbcomp and fresh Xlib maps; refuse trailing `€` with zero events/emissions; invoke candidate planner and emit exact formula once; independently audit all raw/source/artifact hashes in a separate container. No retries.

**D** — PASS only if construction fully confirms receiver focus/control, US baseline parsing, German server/fresh-client transition, and unchanged US control. Formal PASS additionally requires all four receiver/focus controls, all three active German maps plus US control, fail-closed unsupported text, exact formula text and planned press/release trace, empty verified release, and independent integrity audit. Any setup/construction uncertainty is STOP/HOLD and conveys no candidate outcome. Incorrect text/events/safety/release is FAIL.

**C** — OrbStack Docker on Linux/arm64, image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, network none, read-only source/root, separate writable outputs. No host display/input, GUI app, package installation, model or production-source modification. Candidate source is bound to the current-main commit and backend blob recorded in `source_manifest.json`.

**U** — Exact X11 backend, pinned Xvfb and standard German two-level XKB only. No Calc/task effect, physical keyboard, IME/Compose/dead-key/level-3, other layout/backend, performance or product claim. Combined `-noreset` plus connected-client behavior is not a causal comparison.

## Construction gate

The construction test is not formal evidence. It creates fresh private X servers, proves the explicit InputOnly receiver control, applies German while a client remains connected, checks server query/dump and a fresh Xlib map change, and verifies the independent US control is unchanged. Formal may start only after this complete test passes in the pinned image.

## Freeze record

- Base main: `8e82c5bf25d63c70c188d972cdf320533bf4b310`
- Candidate backend blob: `9cae101a219348077668c8fc086acf8e13154afe`
- Runner SHA-256: `2d43c9eca291171007525c24bd9830c77b539f53782ccba42a96eb9deca82532`
- Source manifest SHA-256: `44c5b93c95b89e8425e68cdfcef6d51af42a15cf83cfba277fbc14b70ca178bb`
- Auditor SHA-256: `8c8c4ce296820df45a950e99dbf245ced190244c80ced4dda1a2eb8e88a56938`
- Construction test SHA-256: `60327c7cde14950e9d62a59a85d5bcbd3198e354f24ce7b765aecddf5ba1cc32`
