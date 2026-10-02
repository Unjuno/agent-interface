# #5352 T15 construction report (not a formal result)

Disposition: `CONSTRUCTION_PASS_ONLY`. Five host construction tests pass against the exact GitHub branch snapshot. No formal candidate CLI, independent auditor CLI, or WSLc container was invoked; counts remain candidate=0, auditor=0, formal containers=0, retries=0.

## Exact tested source

Branch: `research/planner-hysteresis-5352-effect-qualified-t15-20261003`  
Tested commit: `ab2abb0bffb2b98729b9ffaaaf37702a18c44085`  
Runtime: Windows x64, CPython 3.11.9, standard library; zero seed.

SHA-256 (UTF-8 file bytes):

- `cases.json`: `f4929456a6bbffece5db25937d4f3fa6780c00a2df6e7d75b34d76da1302f07f`
- `candidate.py`: `3bf870a182260f9b5023cc51c09be61a8920820c540d9d38808c9f2bbf5817c4`
- `auditor.py`: `53f5d91df5706032cb3248dc0fd57baa40f6e8e7191ba05a8c44237200c7e4a8`
- `test_contract.py`: `f7541322738b315b84ab47501b12d9f3fbd8dd9e7783f25848b37ab3598a8a1d`

## Command and outcome

```text
python -B -m unittest research.analysis.planner_hysteresis_5352_effect_qualified_t0_20261003.test_contract -v
Ran 5 tests in 0.008s — OK
```

The tests cover frozen case identity/shape, policy schedule shape, raw-only reconstruction of the planted benign/harmful/unsafe-prefix witnesses, and rejection of a changed schedule bit and a missing row. The expected scoped fixture label tests only whether this finite oracle distinguishes the planted conditions. It is not task-performance evidence and does not validate any real workload effect.

## Execution hold

At the latest read-only local check WSLc 3.0.1.0 responded with 0 running containers; RTX 3080 showed 0% utilization / 11 MiB. Those snapshots do not allocate the shared CPU/container lane. #5085 has no exact #5352 assignment in the latest retrieved coordination comments; the WSLc bridge identity attribution recorded in #5955679326/#5955720978 is also unresolved. Therefore the preregistered separate WSLc candidate/auditor sequence was not launched. Preserve this as HOLD, not a scientific PASS/FAIL. Do not start without a fresh exact-source/main/image/resource gate and an explicit non-overlapping allocation.
