# Issue #59 WSLc Ollama model-store boundary — allocation A01 STOP

## H / T / D / C / U

**H.** A WSLc container using an already cached Python image can mount the existing Windows Ollama model store read-only with networking disabled and observe the three frozen Qwen model manifests plus all declared blob paths and byte sizes.

**T.** The prepared one-shot protocol uses the immutable cached Python image, `--pull never --network none`, a read-only `/models` bind mount, read-only source/fixture, and a separate output directory. Candidate reads manifest bytes and stats referenced blob paths; it does not read/hash model blobs. An independent raw-only auditor runs in a separate container only after candidate exit 0. The construction suite predeclares four mutation checks.

**D.** A scoped pass requires exactly one read-only `/models` mount record; exact manifest coverage and hashes; matching descriptors; every referenced blob a regular non-symlink file of declared size; candidate and separate audit exit 0 with no audit errors; and all four mutations rejected. Missing or mismatched evidence is STOP/FAIL without retry.

**C.** The intended environment is Microsoft WSLc 3.0.1 and cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`. WSLc previously warned that cgroup/swap enforcement is unavailable, so the requested 512 MiB is not an effective-memory-limit claim. The model store remains the existing Windows store and is not modified.

**U.** Even a future mount-boundary pass would establish only read-only manifest/blob metadata visibility. It would not prove Ollama can load these models, that a container can reach Ollama, or any inference, GPU, game, useful-feedback, control, or Issue #59 exit claim.

## Disposition

`STOP_NOT_LAUNCHED_SHARED_WSLC_STATE_AND_NO_ALLOCATION`

No candidate or auditor container was launched (0/0); no retry occurred. The current-main #59 record still says the exclusive bounded WSLc allocation is pending/unassigned. The latest #5085 coordination record reports an attribution-unresolved WSLc bridge identity change during parallel work and explicitly says no further WSLc invocation is planned until the shared-runtime anomaly and allocation conditions are reconciled. That remains the stop boundary for this package; this STOP is not evidence that read-only mounts fail.

The coordination evidence is [#5955679326](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5955679326) and [#5955720978](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5955720978). The latter explicitly says no further WSLc invocation is planned until reconciliation. WSLc shares the physical host GPU, though this metadata-only test needs no GPU. Idle GPU/container snapshots do not grant an allocation. No runtime state was changed here.

## Construction-only checks

On 2026-10-03 JST (2026-10-02 UTC), the five-test synthetic auditor contract suite ran directly in Arch WSL Python (not a container): 5/5 passed. It accepts one valid fabricated raw record and rejects fabricated writable-mount, manifest-hash, missing-model, and blob-size mutations. This does not execute or validate the candidate against the Windows model store.

The prepared host fixture inventories three local manifests and 16 referenced config/layer descriptors by manifest bytes and file metadata only. These are prelaunch inputs, not candidate observations; no blob contents were read or hashed.

## Next admissible step

Keep the prepared package and this STOP unchanged. Resume the one-shot WSLc candidate only after the #5085 owner records an explicit exclusive allocation and reconciles the shared WSLc state. Refresh current-main/source/image identities and mount-path availability before freezing. If candidate exits nonzero or its evidence is incomplete, retain STOP/FAIL and do not run the auditor or retry. If candidate exits zero, run the separate frozen raw-only auditor once.
