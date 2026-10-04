# V39 unknown outer adapter rows — saved experiment record

This package accompanies the current-head follow-up to the V39 duplicate-edge receipt regression. It tests an additional boundary: an unrecognized outer event name carrying `physical_key_measurement` must not disappear from a receipt that otherwise pairs DOWN and UP.

The production candidate starts from #7602 at `a7f9e9e3c4bd31199bde3a14761783ead619ad08` and the #7690 duplicate-row test commit `73ccfa7696c1b005be7c1c59e63d1c06dfe3674d`. The candidate treats unknown outer event rows carrying adapter evidence as unsupported receipt evidence and makes that identity's receipt incomplete. The test keeps a known DOWN/UP positive control and covers unknown-name duplicate DOWN, duplicate UP, and unknown-only rows.

`raw/red-result.json` records the expected baseline red (three assertion failures, zero errors). `raw/green-a02-result.json` records the candidate pass (one method, three cases, zero failures/errors, compile pass). The original green freeze transcription STOP and all auditor STOPs are retained in place. The A05 auditor is **not a PASS**: its mutation-control check found that the validator does not reject its purported frozen-source-hash mutation. The regression result remains useful scoped evidence, but the independent-audit gate is unresolved.

The baseline and candidate inputs, fixture and test runner hashes are bound in `src/red_freeze.json` and `src/green_freeze_a02.json`. The independent-auditor attempt and its own input hashes are in `src/audit_freeze_a05.json`; run command, logs and exit code are under `audit-a05/`. Candidate and auditor pre/post WSLc inventories are retained. WSLc reported swap-limit enforcement unavailable, so no swap-bounded memory claim is made.

This is a deterministic pure-projector construction check against one retained synthetic trace. It does not establish live X-server key release or dwell, application consumption, useful task effect, recovery benefit, a working game path, or MAP01 completion. It authorizes no live/model/input allocation.

For run-by-run outcomes and scope limits, see `PLAN.md`. `RUN_RESULT.json` is the machine-readable disposition. `SHA256SUMS` covers the package files other than itself.
