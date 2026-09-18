# T2 live X11 current-effect receipt handback formal result

Issue #1494. Formal invocation 1; reruns/replacements/tuning 0. Four immutable batches, 16 matched pairs / 32 private-X11 cases.

## Disposition

`PASS_CURRENT_EFFECT_RECEIPT_HANDBACK_SCOPED`

The #1472 actuation-receipt baseline reproduced a visible post-handback effect tail in 16/16 cases. Waiting instead for an independently produced, case-local typed current-effect receipt closed that measured tail before handback without reopening physical input occupancy.

## Frozen results

- ACTUATION_RECEIPT_DRAIN: effect after handback 16/16; local completion after handback 0/16; possible/guaranteed physical occupancy after handback 0/16; correct/released 16/16.
- CURRENT_EFFECT_RECEIPT_DRAIN: effect after handback 0/16; local completion after handback 0/16; possible/guaranteed physical occupancy after handback 0/16; typed effect receipt valid 16/16; correct/released 16/16.
- Candidate extra wait after actuation receipt: p50 **2.055852 ms**, max **3.751476 ms** (<10 ms gate).
- Candidate total frontier-return→handback max: **12.268264 ms**. This total was not the preregistered speed gate; only added effect-receipt wait was gated.
- app delay 0 ms candidate extra wait: p50 **0.576607 ms**, max **0.774305 ms**.
- app delay 3 ms candidate extra wait: p50 **3.516424 ms**, max **3.751476 ms**.
- Construction controls: valid receipt accepted; stale generation rejected; mismatched initial-source hash rejected.
- Independent audit PASS; errors [].

## Integrity

FORMAL_RESULT SHA-256 `f18bb2840943daa83fc7ffcbca8588c4533f14b405f87bb8df1df01e429135a5`. Gzip SHA-256 `eafc024cb26fa0513210b553dce445dfc5ed24067f4e7daa9553b0c291f44a9e`. AUDIT SHA-256 `0d0c671e2389bb34baa2482c291728e6fe04e2dd4d0dab6c2b9f1e83234a4a09`. Batch hashes are retained in `FORMAL_SUMMARY.json`; full rows are retained as `FORMAL_RESULT.json.gz.b64`.

One preformal publication defect was detected and corrected before formal: the first remote `experiment.py` bytes did not match the exact construction source. Formal remained 0; the file was corrected, and final Git-blob readback matched the construction source before any formal batch ran.

## Scope

This is one same-host private X11/Tk F8 fixture. The typed receipt proves only the scoped current pixel transition bound to the case-local window/generation/source bytes. It is not general semantic task completion, does not grant input authority, and does not establish MAP01, model/token, cross-backend, human-tempo, or production behavior.

## Successor

The next useful rung is not another retry of this fixture. Test whether a typed *semantic/current-evidence* receipt can provide the same clean handback in a real application transition where pixel change and task-relevant completion can diverge, while preserving the same no-authority receipt rule.
