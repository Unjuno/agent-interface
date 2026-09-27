# Construction-only record — Issue #4479

This phase is strictly non-formal. It must not invoke `runner.train`, `runner.main`, or the host orchestration `formal.main`. Construction tests cover the non-overlapping seed-component schedule, deterministic synthetic generators and teacher, data-only package schema/digest rejection, lossless compressed fixture transport, and Docker command isolation. No seed is fit and no held-out score is computed.

The source is adapted from merged #3890, not from its dirty local worktree. The exact #3890 main-branch files and their blob hashes are listed in `SOURCE_PROVENANCE.md`. The new independent audit additionally reconstructs the seeded inputs/labels and model predictions from package tensors, binds both loader reports to the exact package raw SHA-256, checks package hashes before/after loaders, rejects duplicate JSON keys/nonfinite tensors, and verifies its own frozen source hash.

Construction Docker command (after source/tests are frozen, before formal freeze):
```powershell
docker run --rm --pull=never --platform linux/amd64 --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m --pids-limit 64 --memory 2g --cpus 1 --mount type=bind,source=<source>,target=/src,readonly --workdir /src --entrypoint python needle-pilot05:local -B -m unittest -v test_construction.py
```

Formal training has not run. Preserve construction STOPs and fix only before the public freeze; after formal begins, no retries, tuning, or seed replacement.

