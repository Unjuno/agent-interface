# Independent #4544 enriched-receipt audit — result

**Disposition: `PASS_ENRICHED_MONITOR_RECEIPT_TRANSLATION_AUDIT_SCOPED`.**

The host run and the pinned OrbStack container run each passed all 8 audit tests. The same container also passed all 11 existing `observable_signal_guard_v2` and `final_action_admission_v1` tests from main after verifying their Git blob hashes. No game, model, GUI, GPU, input, or formal MAP01 allocation was run.

## What was exercised

`monitor_event()` invokes main's real `ObservableSignalGuard` and `ObservableSignalPolicyMonitor.observe()` with a deterministic extractor and a patched `perf_counter_ns`. It therefore emits the production monitor envelope (`sequence`, `signal`, metadata-rich `outcome`, receive/extract/evaluate timestamps, and stage durations) rather than a hand-authored top-level fixture. The missing predecessor event time is explicitly synthetic: host `8577269502000` ns.

The retained iteration-8 probes produce the conservative interval `[-739170084874, -739169181060]` ns, width `903814` ns. The monitor event is 2,362,750 ns from the latest calibration endpoint, within the 5 s limit. Mapping with the latest-possible upper offset gives runtime timestamp `7838100320940` ns, 1,465,019 ns before decision runtime `7838101785959` ns and after planner terminal runtime `7838099328334` ns. The existing final-admission helper returns `REJECTED_POLICY_INVALIDATED`; `input_authority_admitted` is false and `executor_admission` is null.

All original envelope and nested signal/outcome metadata are retained. The original host timestamp is copied to `outcome_evaluated_host_ns`, the translated value is tagged `runtime_monotonic`, and the receipt is tagged `synthetic_monitor_event_missing_from_predecessor`. An extra nested extension field also round-trips unchanged.

Negative controls cover unconverted mixed-domain input, wrong session, fewer/more than three probes, >1 s uncertainty, stale probes, future receipt, missing required field, and authority-granting outcome. All refuse as required.

This audit does **not** independently reproduce the predecessor formal adapter's reported exact-key rejection: the merged #4542 `policy_clock.py` itself requires a subset of keys and preserves extras. The offline audit verifies the enriched path and final gate, but cannot claim that the previously consumed formal STOP was caused by this converter; #4544 seed 990641 in fact stopped earlier at the existing action-validity clock boundary.

## Iteration log

The first candidate run produced 7/8 PASS and exposed that the audit wrapper did not bind the supplied calibration record to a session identifier; its wrong-session negative control therefore did not fail. The wrapper was corrected to require a record-level session binding. The corrected host and container runs both passed 8/8. This is retained here as a candidate-test failure followed by a corrected scoped pass; it is not a formal allocation retry.

## Reproduction

From the repository root, with the two main helper modules and this audit path present:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest research.doom.map01_enriched_receipt_audit_4544_v1.test_receipt_translation_v2 -v
docker --context orbstack run --rm --pull=never --platform linux/arm64 --network none --read-only --workdir /study --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,source="$PWD",target=/study,readonly --entrypoint python issue2679-map01-runtime:20260921-pinned -m unittest research.doom.map01_enriched_receipt_audit_4544_v1.test_receipt_translation_v2 -v
```

The actual local run mounted `/tmp/map01-receipt-4544-input` read-only at `/study`; the container command above is the repository-relative form for integration workers.

## Hashes and boundaries

- `receipt_translation_v2.py`: Git blob `77f3147b013b38d106c23d44b81870c020a52648`; SHA-256 `9a7e131b0421ff78816047b9603f40e4b8a5281e2c7a5bf8f5df7c742ca7db59`.
- `test_receipt_translation_v2.py`: Git blob `e5f7e7b3e3f2b69f35467b7920ca27ed972b2c8a`; SHA-256 `02acbbe3452bda2901ec5106dbf46669903fe0cfc193e9979fa9885e8116893b`.
- `PLAN.md`: Git blob `19d57485c6a4a631ee546ebfc634cd4e7dbe6f21`; SHA-256 `59ec42836306954de566880b1771871bc9402a1705ae2c3922d8054a20c8a817`.
- Main `observable_signal_guard_v2.py`: blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`.
- Main `final_action_admission_v1.py`: blob `2b3875c5c885fac0a78db2e70cbaba30ca834c67`.
- Main `policy_clock.py` from merged PR #4542: blob `bdc2186c7a2cd0861519ed4d12d7cb021616be88`.
- Retained probe JSONL: blob `c78c12917fdbc2ad09280878090dca9d26b60976`.
- Image: `sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e` (`linux/arm64`), Docker context `orbstack`.

This audit does not revise #4544's consumed seed 990641 HOLD, does not recover the historical invalidation receipt, and does not establish a gameplay or MAP01 result.
