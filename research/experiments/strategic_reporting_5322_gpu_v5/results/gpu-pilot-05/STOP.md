# GPU pilot-05 STOP — CPU fallback and call-event readback mismatch

Issue: #5434  
Frozen allocation: six calls / 96 rows, no retries.  
Consumed: **one completed model call** (Qwen2.5 3B, metadata_only); calls 2–6 were never issued.  
Outcome: **STOP — the model ran on CPU, and the controller's initial exact frame readback comparison failed. No GPU result or behavioral conclusion.**

The first response completed with HTTP 200 and the frozen Qwen2.5 digest. Its event contained 16 UNKNOWN rows. The framed event was written to GitHub at `capture/call-01.frames`; the controller's byte-for-byte comparison against the live PTY buffer failed, so it sent no ACK for call 1. It later recovered the stored frames and verified the 561 data-frame sequence, 13,449-byte payload length, embedded SHA-256 `637974ce30e7116c957f536543a49ece2cb350e600502663b6ad4ebf967bac39`, 16 decoded rows, and exact raw-line/row agreement. The decoded event is retained at `calls/call-01.json`. This later recovery does not retroactively satisfy the required live readback barrier; the next call was not authorized.

Call-adjacent `ollama ps` reported `100% CPU`; after stopping, `ollama ps` continued to report `100% CPU`. `nvidia-smi` showed the RTX 3080 at 0% utilization and 0 MiB used. The preregistered GPU-placement requirement failed. The model must not be described as having run on the GPU.

No full allocation audit ran because the pilot did not reach its completion status. No aggregate result, GPU success, calibration, strategic-incentive, safety, equilibrium, or production claim is made. No inference retry or replay was made. Preserve this partial response and STOP unchanged. Any continuation needs a new successor issue, fresh seeds, and read-only diagnosis of Ollama GPU placement plus a repaired exact readback controller before another model request.
