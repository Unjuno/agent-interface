# Issue #8544 T0 A02 result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen candidate and raw-only auditor each ran once, with exit 0 and no retry, under allocation `UNJUNO-8544-CROWDING-T0-A02-20261009`. The freeze is commit `4986fd0affb719a51527fdace8e41584076b21db`; the current-main anchor is `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`. Runtime was host macOS 27.0 arm64 / CPython 3.14.5, standard library only; no container was used or required.

The candidate emitted 5,632 planted cases. The independent auditor reported zero errors across 128 factor strata and 6,341 checks, verified development seeds 0–5 and held-out seeds 6–7, and rejected all seven mutation controls, including a payload factor changed while retaining its old fixture ID. Endpoint class counts were: correct binding 512; neighbor substitution 512; miss 512; abstention 1,024; schema error 1,024; ambiguous identity 1,024; correct rejection 512; false alarm 512.

Candidate raw SHA-256: `7df299372b506143ceec2a19f03dcb2a0ac61407d39cf802a1f4c8985e36d4f8`. Audit output SHA-256: `4c34da944ce1afc133277a4d92bb774bf5b9efca2926b8704e6ce1fba39e9bab`. Invocation receipts, stdout/stderr, exit codes and output hashes are retained under `results/`; their hashes are in `RESULT_SHA256SUMS.json`.

This validates only the deterministic planted-endpoint scorer, factor ledger and one-shot output custody. It does not test an image renderer, human perception, a VLM, spacing effects, predictor performance, crowding-like transfer, GUI behavior or runtime adaptation. The endpoint classes were authored into the fixture, so the measured counts are not empirical model outcomes. A01's pre-process launch STOP remains unchanged.
