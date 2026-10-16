# T2 X11 A2 — absolute deadline after effect-receipt wake

Issue #1518. Formal invocation 1; reruns/replacements/tuning 0. Four immutable positive batches (16 matched pairs / 32 cases) plus one immutable four-case NO_EFFECT batch.

## Disposition

`PASS_CURRENT_EFFECT_ABSOLUTE_DEADLINE_SCOPED`

The #1492 deadline-enforcement gap is closed in this same-host private-X11 fixture by re-checking the absolute monotonic deadline immediately after each effect-receipt queue wake. No timeout or latency threshold was loosened.

## Frozen result

- ACTUATION_RECEIPT_DRAIN reproduces the discriminator: independently visible effect after handback 16/16; correct/released 16/16.
- CURRENT_EFFECT_RECEIPT_DRAIN: effect after handback 0/16; local completion after handback 0/16; possible physical occupancy after handback 0/16; correct/released 16/16.
- Typed effect receipts observed 16/16 and completed handback 16/16. Late accepted receipts: 0/16. Positive strict-deadline timeouts: 0/16.
- Candidate receipt wait: p95=max **3.835944 ms**, below the frozen p95<6 ms / max<8 ms gates.
- Minimum accepted deadline margin: **4.164056 ms**.
- app-delay0 candidate wait: p50 **0.578857 ms**, max **0.787520 ms**.
- app-delay3 candidate wait: p50 **3.481375 ms**, max **3.835944 ms**.
- NO_EFFECT controls: effect receipts 0/4; completed handbacks 0/4; explicit unresolved timeouts 4/4; correct/released 4/4.
- Independent audit PASS; errors [].

## Integrity

FORMAL_RESULT SHA-256 `d0058b69c294571de47a5091a00d37d37ecfb0de61e99a0b9bdc1a3fb37f8c57`. Gzip SHA-256 `22fbd3251aa3094bc862dc6f53ffcd2b248cbf664ad66de21db5a1d11b5f4bd6`. AUDIT SHA-256 `9fc57e73d8585f52ef080af0ef58fb53fc04c1525c12c30efcdb653184c7d4dc`. Batch hashes are retained in `FORMAL_SUMMARY.json`; full rows are retained as `FORMAL_RESULT.json.gz.b64`.

The exact parent #1492 source was SHA-verified before the one-factor patch. Source publication/readback matched 8/8 Git blobs before formal. A deterministic helper control also returned a matching receipt only after its deadline and was rejected. #1494 is a closed coordination-invalid duplicate and is not pooled.

## Scope

This PASS establishes only that an absolute post-wake deadline check closes the previously observed late-acceptance implementation gap while retaining #1492's scoped current-pixel effect handback behavior on one private X11/Tk fixture. It does not prove general semantic task completion, scheduling guarantees on other hosts/backends, MAP01 behavior, model/token gains, or production readiness.

## Next rung

Do not retune this timeout or repeat the same F8 fixture. A useful next discriminator is transfer to a real application transition where the receipt is tied to task-relevant semantic/current-evidence completion rather than a single pixel change, preserving the same absolute-deadline and no-authority rules.
