# T1 first candidate outcome — preserved STOP

Allocation: `LOGICAL-TIME-SYMMETRY-7327-UNIT-T1-20261004-01`
Frozen main: `4d42238694c55aaa29bf47cb13a5b8d4c5d4074a`
Candidate source SHA-256: `63db6fbd98d2658b3746c3c562d03672f1933a8883564778cd72aa7375263116`
Spec SHA-256: `2795da79b891893e47afaa079762331b2b3f985a0626c2cd015aafda3822bcbb`

## H/T/D/C/U outcome

- **H:** Not tested; the candidate stopped before it produced any representation pair or logical trace.
- **T:** Exactly one host invocation of `python3 candidate.py spec.json output/candidate.raw.json`, Python 3.14.5, standard library only. No container, GUI, model, input, network, or retry.
- **D:** `STOP_CANDIDATE_INPUT_SCHEMA_MISMATCH`. Candidate exited 1 on the first scenario with `KeyError: 'reference_period'`. The frozen spec places this field at the top level, but candidate `encode()` reads it from each scenario. No candidate raw file was produced; independent auditor invocation count is zero because there is no candidate output to audit.
- **C:** This is a candidate/schema integration failure, not evidence for or against unit-representation symmetry.
- **U:** All unit-conversion, trace-equivalence, and mutation gates remain untested.

Exact captured command result:

```text
Traceback (most recent call last):
  File "/Users/taka/Documents/Codex/2026-10-03/agent-interface-r134-feedback-audit/research/analysis/logical_time_symmetry_7327_unit_t1_20261004/candidate.py", line 125, in <module>
    main()
    ~~~~^^
  File "/Users/taka/Documents/Codex/2026-10-03/agent-interface-r134-feedback-audit/research/analysis/logical_time_symmetry_7327_unit_t1_20261004/candidate.py", line 113, in main
    encoded = encode(case, unit)
  File "/Users/taka/Documents/Codex/2026-10-03/agent-interface-r134-feedback-audit/research/analysis/logical_time_symmetry_7327_unit_t1_20261004/candidate.py", line 26, in encode
    "time": {name: fmt(q(case[name]) * multiplier) for name in FIELDS},
                         ~~~~^^^^^^
KeyError: 'reference_period'
```

The frozen candidate/spec files remain unchanged. Any corrected run requires a new allocation ID, new source hashes, and a distinct additive path.
