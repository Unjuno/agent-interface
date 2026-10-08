# T0A preregistration — independent offline receipt audit

This is a separate offline audit allocation for the already completed T0 build/run smoke. It must not re-run or alter T0; a T0A STOP would qualify only the receipt audit and would not rewrite the T0 first outcome.

## H / T / D / C / U

- **H:** An independent verifier can validate the three frozen source files, build output, run receipt, post-run inventory summary, and T0 run record; it will accept the intact bundle and reject a changed payload hash, surviving named container, mutated probe source, or missing cached-base evidence.
- **T:** The five-test suite is construction evidence and has already passed. Freeze the auditor/tests and evidence inputs below, then run exactly one `python -B audit_t0.py --root .`. This audit reads local files only. WSLc builds/runs=0; Docker runs=0; audit CLI maximum=1; retries=0.
- **D:** `PASS_T0_RECEIPT_AUDITED` only if the one audit invocation exits 0, reports the fixed source/result identities and one build/one run/zero retries, and all frozen-input hashes validate. Any exception or mismatch is the first T0A STOP with no retry. T0's original build/run result remains separate and unchanged.
- **C:** Expected source hashes were fixed before T0. The run output contains the observed host cgroup/swap warning and the independently checkable payload SHA-256. The image ID is compared across build output, run record, and post-run image inventory. Tests mutate temporary copies only; they do not touch the retained T0 files or run a container.
- **U:** T0A validates this receipt bundle only. It cannot measure runtime performance or memory, establish an effective memory limit, prove broad Dockerfile/Compose/Engine API parity, or upgrade T0 into an application-workflow migration.

## Frozen audit inputs

| Input | Bytes | SHA-256 |
|---|---:|---|
| `audit_t0.py` | 5,783 | `7fdfaf9ad1505e9bbfde8aedaf845fc18d8c0f683509cc4d008e81d97e0112eb` |
| `test_audit_t0.py` | 3,764 | `3dd893c1d18d9089b863e7b6ae507fad9e49faa101a5937313b09f4df77b7c23` |
| `Dockerfile` | 336 | `ec8ab4d198d4a6cfc163e9cbd4098c7d68b86f0fa14f870fa5d8addee310352d` |
| `payload.txt` | 36 | `3280e32e693397e74af56b9f9f0dd473dd663224a3c62883b33cbc8828d7c383` |
| `probe.py` | 819 | `78a615ffacc99f453c7f81995db92d962ec0ec60069ebc3415d0a89ddcc20893` |
| `build.output.txt` | 511 | `a76aa6cbfdd50dd50c647e6c582c4577115298ea1a2c102fa63bf7df84e37b4d` |
| `run.output.txt` | 350 | `207e6eb72a3e616cca690fb8bb7477bef4139923224690bf49490285efcde227` |
| `POSTRUN_CHECK.json` | 491 | `9e512438029a0da95f88fc5078c7fca730ddc03d0eea90d39cadced8588c563f` |
| `RUN.json` | 2,188 | `518bc8c0a831d1dbc5443459d520167cd51f98241f5d3a1067c80674671fba88` |

The construction suite ran after auditor implementation and after the final source edit: 5/5 tests passed, including the four mutation cases. The single T0 build/run is not part of T0A and will not be repeated.
