# A03 result

Disposition: PASS_METHOD_SCOPED_A03.

The exact A02 candidate and independent auditor sources were invoked once each in separate, network-disabled WSLc Node containers using the A03 allocation identity. Both exited 0; retries=0. The candidate reconstructed 30 rows with eligible weight 3. The independent auditor reconstructed the exact multiset and rejected 11/11 registered mutations.

| Measure | Candidate | Independent oracle |
|---|---:|---:|
| Proximal assignment effect | 1.0 | 1.0 |
| Distal assignment effect (higher is better) | -2.0 | -2.0 |
| Unweighted/no-carryover contrast | 1.4999999999999996 | 1.4999999999999996 |
| Pooled propensity-weighted effect without explicit history model | 1.0 | 1.0 |
| Executed-only contrast | 4.0 | 4.0 |

All four support/window/eligibility/interference controls returned NONIDENTIFIABLE. No task-success claim was made.

Candidate source SHA-256: e7fd497f01c9c57c80e84acecf5e0fec574865ba0156da9d1459a1bbd477dca8
Auditor source SHA-256: 475e4c939803b29d42d08f768a44cb3536c92ac25f2a8603a82b6041318ab9f5
Fixture SHA-256: 22f35b4b1dabe4eb532abd7a1db9ea72c936a51ee4e10ff40c17c1525f667735
Runner SHA-256: 67aad0648dfeae0dccaae0ef580abd8d9661c7113a5e1ac151d3680a7e017ae8
Candidate raw SHA-256: ef50bd0825c1db59703250cace78b0692d6a9d5be8d211a238741b1ff6424422
Audit raw SHA-256: a054ca0cdf2ab99c05fc1736c487573f981ad204c3f0a07e299df84328fd9f2c

Exact commands, runtime/image IDs, stdout and raw streams are retained alongside this result and in [Issue #7834](https://github.com/Unjuno/agent-interface/issues/7834#issuecomment-5986196185).

This replay verifies reproducibility and container execution for this authored finite method fixture only. It does not add a new estimator, empirical trial evidence, user benefit, GUI correctness, safety, or task-effect claim. A01 and A02 remain unchanged; their host-V8 deviations remain in their own historical records.