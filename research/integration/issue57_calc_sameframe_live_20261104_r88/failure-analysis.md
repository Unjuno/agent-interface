# r88-a01 failure analysis

## Result

The sole preregistered live attempt ended `FAIL_OR_UNKNOWN` before input. The compiled call returned `CALC_REVIEW_SOURCE_STALE` with `input_dispatched=false`, `operation_invoked=false`, and `replay_allowed=false`. No task effect or input release claim is available. The saved Calc target was terminated during host cleanup; its clean-exit receipt is false/unknown. No retry was performed.

## Source-level cause

The retained `review.json` returns a successful `reviewed` receipt with source sequence 1. Both retained mint receipts also use sequence 1 and report `minted`. In `runtime/cli_v1/mcp_guarded.py`, `interface_guarded_calc_compiled` rejects unless the module's `latest_calc_source_sequence` equals the reviewed sequence and both aliases are present in `minted_calc_aliases`. `interface_guarded_observe` updates that module-local sequence and clears aliases. Before this change, `interface_guarded_review_window` only returned `submit(...)`; it did not update the local sequence or ledger. Thus the normal launch -> review -> mint entry/save -> compiled Calc path had no locally current source and no aliases registered for the compiled gate, even though review and mint calls had succeeded. The underlying source freshness checks remain necessary and unchanged.

A code fix and synthetic regression test are in the companion branch: a successful review now records its returned positive source sequence and clears aliases, matching successful observe semantics. Failed or malformed reviews do not update the ledger. The new test verifies review -> two same-sequence mints -> compiled request reaches the existing submit path. This is offline evidence only; a separate preregistered live attempt is still needed to prove the target path.

## Audit limitations

The frozen `audit.py` expected `ROOT/r88-a01`, but the frozen invocation ran it from `/evidence/r88-a01/audit.py` with the packet root mounted at `/evidence`; the audit therefore looked for a duplicated `r88-a01/r88-a01` directory and could not write its report. The original frozen audit file remains unchanged and its SHA-256 remains in `FREEZE_SHA256SUMS.txt`. `audit-adapted.py` changes only the input-root and output-report paths so the frozen gates can be evaluated against the retained packet; the resulting `audit-adapted.json` is `FAIL_OR_UNKNOWN` and is not represented as the frozen auditor's original run.

The container was invoked with `--rm`. Its daemon `die` event was no longer available when evidence finalization ran, and the host wrapper threw before writing `docker-exit-code.json`. The exit code is consequently recorded as unknown; it is not reconstructed from inference. `docker-host.stdout.txt` retains the runner traceback. Do not infer container stability from this failed task path.

## Scope

This is one scripted Docker/Xvfb Calc attempt with no provider/model use. It does not establish task success, release after input, clean target exit, bounded recovery, comparative efficiency, WSLc, MAP01, broad reliability, or product completion.
