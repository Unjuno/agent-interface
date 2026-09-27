# Formal result audit

Run 35444087832 executed the generation-bound evidence harness once inside python:3.12-slim on Ubuntu Actions. Docker setup, container execution, independent audit, and artifact upload all passed. The sequence was ENCODED, OBSOLETE, CACHE_HIT, ENCODED; cache reuse bytes were identical and the stale-unchecked control was rejected. Model, X11, and input counters were zero.

Artifact 10585146161 digest: sha256:a8634e1f92013b904da8e153c42d586487b76c745b0afe6c946e92daff7d9db6.

This is only container reproducibility and generation bookkeeping. It does not establish live PNG/X11 capture, model-facing value, latency, task correctness, or transfer. Prior #2047 HOLD remains unchanged.
