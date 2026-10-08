# T1 construction record (not formal evidence)

- Fixture generation: 32 fixed seeds × four task/route strata × 64 rows = 8,192 unique attempt IDs; oracle stored separately from candidate input.
- Initial WSLc construction command using `pytest` stopped with exit 1 because the pinned Python image has no pytest module. It was not retried with network access or package installation.
- Harness changed during construction to Python standard-library `unittest` only.
- Final local construction: `python -B -m unittest -v test_t1`, 5/5 passed.
- Final WSLc construction: pinned `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `--pull never --network none --cpus 1 --memory 512M`, 5/5 passed.
- WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` No effective memory enforcement claim is made.
- Construction controls confirm confounded gateway exposure, explicit within-stratum no-overlap, missing exposure, successful attempts despite active fault exposure, independent reconstruction, and rejection of five mutations.
- These are construction checks only. Formal candidate and separate auditor are unrun at the time of this record.
