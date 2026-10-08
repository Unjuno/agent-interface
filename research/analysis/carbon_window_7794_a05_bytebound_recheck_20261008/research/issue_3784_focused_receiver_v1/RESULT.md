# Issue #3794 formal-01 result

## Disposition: PASS — scoped German XKB formula delivery

The preregistered allocation ran once in the pinned OrbStack container. Three fresh German XKB rows and one US control all reached candidate completion and delivered the exact KeyPress text `=B2*A2` to the focused InputOnly receiver. This is the first actual candidate-delivery result for the explicit receiver hypothesis; it does not upgrade any predecessor STOP/FAIL or establish application/task effect.

| Row | Server layout verified | Receiver control | Formula text | Events / plan | Unsupported `€` | Release |
|---|---|---|---|---|---|---|
| de-01 | German query + changed server dump + changed fresh-client map | PASS | `=B2*A2` | 20/20 | refused, 0 events/emissions | empty |
| de-02 | German query + changed server dump + changed fresh-client map | PASS | `=B2*A2` | 20/20 | refused, 0 events/emissions | empty |
| de-03 | German query + changed server dump + changed fresh-client map | PASS | `=B2*A2` | 20/20 | refused, 0 events/emissions | empty |
| us-control | US query; dump/map unchanged | PASS | `=B2*A2` | 18/18 | refused, 0 events/emissions | empty |

The receiver control counts character content only on KeyPress. The matching KeyRelease is checked by type and keycode; its `XLookupString` bytes are retained but are not treated as a second character. Unsupported `=B2*A2€` was refused through public backend preflight in all four rows before any backend emission or receiver event. Valid preflight also produced zero emissions/events in all rows.

## Independent audit

- Raw disposition: `PASS_GERMAN_FORMULA_DELIVERY`.
- Independent disposition: `PASS_AUDIT_CONFIRMED_DELIVERY`; integrity errors: 0; setup stops: 0; semantic failures: 0.
- All five corruption challenges were rejected (wrong candidate source, dropped row, altered artifact hash, wrong KeyRelease lookup, forged candidate PASS); the separate early-STOP phase check passed without requiring uncaptured maps.
- Source base: `1355ff9c0e89e04887e7dd3a08aaa93c7b650df0`; candidate blob: `9cae101a219348077668c8fc086acf8e13154afe`.
- Runner SHA-256: `604ff7238e7ba6053456787520696589bbd7cd9d6ffc877fe771b2ab82d7eb50`.
- Source manifest SHA-256: `34be24b090cbcaec586613a868ecd7a16008d8977b4f7073c9dee70d593e8a6d`.
- Auditor SHA-256: `99ea3659b837f6c81db653a945fdd8a4cf360e67acb74626ee459bd765141c02`.
- Raw JSON SHA-256: `369b4d98e1e4ea9cdbfaea8709875a3044fde22308415bd856dfe675464e6c4f`.
- Audit JSON SHA-256: `70bc0f0301bfe30775e7dbcc593960c86cbd0501629e873f1d3115068cbe0cd1`.
- Image: `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, linux/arm64, network disabled. OrbStack Docker Engine 29.4.0.

## Reproduction

See [CONTAINER_RUN.md](CONTAINER_RUN.md). Formal evidence is under `results/formal-01/`; the independent audit is under `results/audit-01/`; container stdout/stderr are retained separately under `results/host/`. The formal runner and auditor each ran once in distinct no-network containers. Construction checks were not counted as formal rows.

The preceding #3792 formal-02 harness STOP is preserved unchanged under `results/predecessor-3792-formal02-runner-stop/` with its exact hashes. It is not part of this formal matrix and is not reclassified by this PASS.

## Scope and limits

This establishes only exact X11 backend/XTEST delivery to an explicit focused receiver under the pinned Linux/arm64 Xvfb image, for the standard German two-level XKB map and the single ASCII formula tested, plus one US control. It does not establish Calc or other application semantics, user-task effect, physical keyboard behavior, Compose/dead-key/IME/level-3 behavior, other layouts/backends, reliability rates, latency benefit, or product readiness. Integration workers should independently rerun from the frozen preregistration before promoting this component result into any broader claim.
