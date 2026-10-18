# A04 result

Disposition: PASS_METHOD_SCOPED_A04_QUALIFIED.

The frozen candidate ran once in WSLc; its independent auditor ran once on the saved raw output. Both exited 0; retries=0.

| Quantity | Candidate | Oracle |
|---|---:|---:|
| Rows | 2,600 | 2,600 reconstructed |
| Eligible weight | 2.9999999999999853 | 3 |
| Observed-window rate | 0.800000000000001 | 0.7999999999999972 |
| Arm 1 vs 0 proximal effect | 2.583333333333349 | 2.583333333333336 |
| Arm 2 vs 0 proximal effect | 0.16666666666666777 | 0.16666666666666674 |
| Distal U=0 | 8.44375 | 8.44375 |
| Distal U=1 | 9.443750000000001 | 9.44375 |

Execution fractions by arm: [0.9081632653061221, 0.6388888888888892, 0.6428571428571429]. The independent auditor rebuilt the exact row multiset and rejected 17/17 mutations. All six fixture controls returned NONIDENTIFIABLE.

The freeze wording says five controls, but the hash-frozen fixture contains six; this is preserved and qualified in issue comment 5986498125. All six were tested, exceeding the literal minimum. No task-success claim was made.

Candidate raw: blob 6c91fbb5cfedb8298ee3c9b2232dd6c1fbd28817, SHA-256 b7195bf614f0851798abc3d59551fb7b2e8303b69436ac74d2ef3ded24608d9a.
Audit raw: blob 38d097562a8ca2b8c82f66874871f512284378fb, SHA-256 bbe713bcadec446af7c21349d539eb9bcedae64c4b86dd0a2178c473c5c3582e.

This is one authored finite method case, not empirical MRT or user/task evidence. Construction defects C01/C02 remain preserved; see CONSTRUCTION.md.