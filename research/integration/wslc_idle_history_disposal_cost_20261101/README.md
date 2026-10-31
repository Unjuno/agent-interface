# Detached history copy and disposal on WSLc

The earlier [WSLc fork measurement](../wslc_idle_history_fork_cost_20261101/README.md) excluded disposal after the timed insertion. This follow-up measures fork plus insertion with and without destroying the staged copy while the original history remains alive. Disposal is a proxy for reference-count work, not a measurement of the production publication path or proof of its deadline behavior.

Two fresh WSLc containers used pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, no networking, one CPU, a 1 GiB memory limit and no pull. Both arms and source hashes were frozen before the first run. The snapshot is draft [#10074](https://github.com/Unjuno/agent-interface/pull/10074) commit `0675ab810f7ee890d0904b8a402678c81f8dbafb`; the pre-run main was `3340b453018f2e5f3d4112fb9cb93149ced5daaa`. Each size had 41 paired trials in alternating order; arms used ascending and descending sizes. The inputs are synthetic metadata and a shared 16×16 image.

| Retained entries | Fork + insert, excluding disposal, median ms (ascending / descending) | Fork + insert + disposal, median ms (ascending / descending) |
| ---: | ---: | ---: |
| 0 | 0.0007 / 0.0006 | 0.0007 / 0.0007 |
| 1,000 | 0.0029 / 0.0026 | 0.0044 / 0.0039 |
| 10,000 | 0.0213 / 0.0224 | 0.0351 / 0.0363 |
| 100,000 | 0.5590 / 0.5680 | 0.9168 / 0.9185 |

Both containers returned zero. [raw.zip](raw.zip) contains the source snapshot, frozen conditions, every sample, and launcher output; its SHA-256 is `73ab658cae20e8a4963565b82385dfb3dbee002b8a1f60cd8d6836e16fad9de9`. The packaging audit verified source hashes, conditions, trial counts, alternating order, positive timing samples, recomputed medians, stdout against result, and archived hashes.

At 100,000 entries including disposal increased the measured median by approximately 0.35 ms in both arms. The old published history's actual lifetime and disposal may differ because readers can retain references. There was no capture, disk reload, IPC, model, input, concurrent reader or GUI task; these results do not demonstrate end-to-end latency, input release, task effect or recovery. Disposal, in addition to allocation and copying, must be included when evaluating a history optimization; preserving isolation of readers and cancellation remains a correctness requirement.
