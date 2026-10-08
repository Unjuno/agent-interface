# T1-A18 STOP/INCOMPLETE

A18 did not complete its preregistered allocation. The candidate process was invoked once and exited with code 1 after `OSError: [Errno 28] No space left on device` while flushing the next raw JSONL record. The model response had returned before the failed write, but that response was not persisted. No retry, seed replacement, or repair was attempted.

The preserved raw file contains 231 valid, contiguous rows (IDs 0–230) from the planned 390. All persisted rows identify `qwen3:14b` with the frozen digest, and none records a model-call error. The next response corresponds to row ID 231 and is unrecoverable. The independent auditor was not run because the frozen completion gate requires all 390 rows. No accuracy or schedule conclusion is drawn from this partial output.

The isolated server on port 11435 was stopped. The exact run state and checksums are in `STOP_RECORD.json`; preflight and the append-only partial raw remain under `results/FORMAL_T1_A18/`. After stopping the model service, `df -h /` reported 14 GiB available. That is not treated as proof of the precise disk consumer or as evidence that the host has sufficient headroom for another 14B run.
