# #5279 source archive — formal raw-delivery HOLD

Disposition: `HOLD_RAW_DELIVERY_UNVERIFIED`. This is a source-preservation record, not promotion of a formal result.

## What is retained

- The original branch's 10-file source/plan/environment capsule, 43,307 decoded bytes, `monitor.py`, `worker.py`, `restore.py`, `README.md`, and `FREEZE.json` are preserved byte-for-byte.
- The exact original branch tip `5c2bd2cba7aed9d592a4805271ba64bcb5da68f4` is also preserved by annotated tag [`archive/recovered/verifier-lifecycle-5279-20260929-original-20261002`](https://github.com/Unjuno/agent-interface/tree/archive/recovered/verifier-lifecycle-5279-20260929-original-20261002).
- The historical Issue report records `PASS_TINY_VERIFIER_RESIDENT_T0_SCOPED` for four batches and 64 worker exits ([Issue report](https://github.com/Unjuno/agent-interface/issues/5279#issuecomment-5891531127)). That is an Issue-reported outcome, not an independently re-audited result from this source archive.

## Evidence boundary

The retained source branch does **not** contain the formal raw batch records, the final raw-only audit receipt, or its corruption-control evidence. Consequently this archive cannot replay the reported outcome or validate its formal gate. Keep the result unpromoted and the allocation consumed; do not rerun it to replace missing evidence. The Issue's reported result and this raw-delivery HOLD are distinct facts.

## Read-only recovery check (2026-10-02)

The source capsule restored 10 files / 43,307 bytes from its two recorded parts in a network-disabled Docker container. The restored `test_study.py` suite passed 6/6 under CPython 3.13.5 on Linux/arm64. This checks source restoration and unit contracts only; it is not the original Linux/x86_64 allocation, formal runner, or raw audit. No lifecycle batch was run and no scientific outcome was changed.

The historical README's statement that no formal batches had run at source commit time is retained unchanged. The later Issue-reported outcome does not supply the missing raw artifacts.
