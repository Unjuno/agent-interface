# #5139 construction seed-axis independence probe

Date: 2026-09-29. This is a host-CPU synthetic construction probe, not a model study or allocation.

## H / T / D / C / U

**H.** The dataset builder keeps its three metadata/control dimensions separated: changing only the formal sentinel changes held-out generation/selection but not support rows; changing only the support sentinel changes support rows/selections but not held-out rows/selections; changing only the allocation label changes only that label.

**T.** Ran `python -B research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/seed-axis-independence-20260929/seed_axis_independence.py` from repository root against `make_dataset.build` and the separate `audit_sampler.audit_support_selection`. Four synthetic sentinels: formal 903520260929 / alternate 903520260931; support 903520260930 / alternate 903520260932. No model or dataset artifact from the formal allocation was used.

**D.** Exit 0, `PASS_CONSTRUCTION_SEED_AXIS_INDEPENDENCE`; 10/10 assertions passed, and independent support-selection audit returned no errors for all three seed combinations. Canonical dataset SHA-256 values: base `a1f83d85a87a11abe01693fc82607a1c872bda44cdbce04812c6c0570691f81b`; formal alternate `f1c439fc1908077f1613de72adbdf0722ca93d572ea4796b16cbcf5fb5413928`; support alternate `b251e2c77a8a81b2f85b595a84384c30829b734a2a188bc1fb2908331a4d8385`; allocation-label alternate `f15b99fef24885631eba532ea3d4be23f4121db77f4f9fb7a39f59d0d0402ab8`. Full machine-readable checks and hashes are in `result.json`.

**C.** Same repository builder, fixed deterministic sentinels, only one named input varied per pair, and independent support auditor. This supplements the prior two-point formal-seed control; it is not a second formal run.

**U.** Proves only deterministic construction-axis isolation for this synthetic fixture. It does not establish tokenizer/model behavior, quality, causal effects, GPU performance, or suitability of any formal seed. No CUDA/GPU, Docker/OrbStack, model load, fit, adapter write, or formal allocation occurred. No #5134 CPU slot is claimed; its prior false assignment statement has been withdrawn. #5139 remains without an explicit GPU/Docker lease.
