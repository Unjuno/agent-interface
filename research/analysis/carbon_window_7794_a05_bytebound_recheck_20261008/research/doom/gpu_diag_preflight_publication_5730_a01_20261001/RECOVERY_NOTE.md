# Recovery note — Issue #5730 A01

This note is additive; the frozen allocation files beside it are unchanged.

- **H / T:** The historical host-only construction gate was intended to reject a frozen-source mismatch before invoking its synthetic candidate.
- **D:** The retained A01 execution record says the wrapper stopped with `STOP_FROZEN_SOURCE_MISMATCH:synthetic_candidate.py`; candidate=0, auditor=0, raw SHA is null, and `scientific_result=NOT_EVALUATED`. This is protocol STOP evidence, not a scientific PASS or FAIL.
- **C:** No GPU/CUDA, model, Docker/OrbStack, GUI, game, input, or formal allocation was used for that stopped invocation.
- **U:** No GPU correctness/performance, live Issue #59 behavior, or device-contention claim follows.
- **Provenance:** The 13 pre-existing package files were recovered byte-for-byte from commit `4ee8334a99b6b0653fd357cd1caeab9078ed70a0`, before descendant `687d6898db28c45705d753116f63e8fb1d4cd770` removed them. The removed commit and original branch are retained; no inference is made about why that deletion occurred.
- **Raw-byte limitation:** The recovered `A01_EXECUTION.json` declares stderr sizes/hashes of 52 bytes / `6f4ee9531f5cec7e4e51ae3117251ce7d9aa70810827357ad5211fe42822ec77` and 2,278 bytes / `8bc1d4d90c99f8660271ff9ca5ac5904fef4b71a9d943f458d1d06c0e519ad75`. The recovered stderr files are CRLF and are 54 and 2,280 bytes; their SHA-256 values do not match those declarations. The checked-out blobs were not edited or normalized. Treat the stderr byte-level provenance as unresolved; do not call those files hash-verified raw output. The empty stdout files do match the declared empty-file SHA-256.
- **Recovery validation:** The package files are copied byte-for-byte from the source commit. The local `test_fail_closed.py` suite (14/14) uses temporary synthetic fixtures; it does not execute the historical `run_construction.py` wrapper or repeat the A01 allocation.
