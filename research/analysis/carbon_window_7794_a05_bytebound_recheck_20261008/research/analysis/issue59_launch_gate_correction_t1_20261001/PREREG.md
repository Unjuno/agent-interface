# Issue #59 launch-gate correction — preregistration

## H — hypothesis

Two narrowly scoped construction defects in the frozen host-only Issue #5730 gate are correctable without changing its historical result: (H1) a successful inventory command with exactly empty stdout represents an empty compute-process list, not a failed/missing inventory; (H2) publication verification failure must not leave an artifact at the requested output path. Missing stdout (`None`), command errors, malformed/nonconforming non-empty inventory, source identity mismatch, invalid candidate output, and pre-existing output must remain fail-closed.

## T — test and treatment

Test the frozen predecessor source at `origin/research/5730-gate-cleanup-fail-20261001:research/analysis/issue5730_gate_cleanup_fail_20261001/gate.py`, whose SHA-256 is `16ee28ef0ee97da19e89de97a3a01e132055023013fb9c2b579a4264462c498c`, against the two positive successor expectations. Then run the same behavioral checks and negative-boundary checks against this additive candidate. The synthetic tamper adversary can rewrite the published file but does not control its containing directory; denied unlink is reported as a cleanup STOP with residue explicitly preserved in the test receipt.

Candidate change accepts `returncode == 0` with `stdout == b""` as `{"compute_processes": []}`; distinguishes `stdout is None`; publishes atomically without overwriting a pre-existing path; and removes its uniquely claimed output after post-publication verification STOP. Unsupported/denied publication must become a typed STOP. Cleanup failure must become `STOP_OUTPUT_CLEANUP_FAILED`. This is a CPU synthetic contract test; no local GPU, model, GUI, game, physical input, or live MAP01 measurement.

## D — decision rule

PASS only if both frozen-predecessor assertions fail for the predicted reasons and all candidate tests pass: empty inventory publishes only with valid source identity; null inventory and nonzero inventory never invoke candidate; existing output is preserved; denied publication is typed; successful output bytes exactly match their recorded SHA-256; post-publication tampering returns `STOP_POSTWRITE_DIGEST_MISMATCH`, `NOT_EVALUATED`, null raw digest, and leaves no output residue. Candidate tests must also verify failed cleanup returns `STOP_OUTPUT_CLEANUP_FAILED` and reports no raw digest. Any unexpected invocation, overwrite, residue, or status is FAIL/STOP, not scientific evidence.

## C — confounds and scope

The tests exercise a Python filesystem contract on the current host only. They do not establish GPU availability, hardware lease, launch correctness, artifact durability under power loss, concurrent writers, cross-filesystem behavior, MAP01 ability, or any task effect. Hard-link publication support is required for this prototype; unsupported filesystems must STOP rather than silently fall back to an overwriting operation.

## U — uncertainty / limits

No formal experiment or scientific result is produced. This is a corrective engineering successor under parent Issue #59, explicitly not a new work order and not a rewrite of closed Issue #5730 or its frozen evidence. Current `main` freeze: `733981dda72414c33d12c0687430989f12366db0`; refresh before merge/PR and re-evaluate conflicts.
