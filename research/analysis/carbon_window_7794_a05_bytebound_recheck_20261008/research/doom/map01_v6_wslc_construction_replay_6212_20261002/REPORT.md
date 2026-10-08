# WSLc replay of the v6 recovery construction suite

## Disposition

`PASS_WSLC_CONSTRUCTION_PORTABILITY_SCOPED`. The exact five deterministic scripts already compared across Windows and ordinary WSL in PR #6212 were each executed once, unchanged, in one WSLc container. All five exited 0 and the expected counts matched. The independent auditor also verifies all 10 Git blob identities and SHA-256 digests against the mounted frozen source.

This is an additive WSLc runtime-portability check, not a new recovery or gameplay result. It does not consume or authorize the v6 formal allocation.

## H / T / D / C / U

- **H:** The five retained construction checks run unchanged under a digest-pinned WSLc container with a declared CPU/memory ceiling and network disabled. **Supported for this source snapshot and these tests.**
- **T:** Detached source commit `14b81dd1f6853623a694266b98538f812847257a`; five subprocesses, one each, in a single WSLc run. Read-only bind mount; no network; CPU quota 2; memory ceiling 512 MiB. Exact scripts and source hashes are listed in `FREEZE.md` and `SOURCE_MANIFEST.json`.
- **D:** All five expected test markers/counts matched PR #6212; each child exit 0; `cpu.max=200000 100000`; `memory.max=536870912`; cgroup `memory.peak=37511168` bytes (35.77 MiB), below the configured ceiling. Separate auditor: zero errors over five rows and ten source files.
- **C:** Compared only logical pass/count outputs to PR #6212's Windows and ordinary-WSL report. The old report did not retain comparable wall-time or memory measurements. WSLc wall times here are descriptive only; no speedup or memory reduction is inferred.
- **U:** Does not demonstrate iteration-speed improvement, comparative memory relief, Docker-to-WSLc performance equivalence, swap restriction, or any formal/live recovery effect. Test sources use fakes and do not exercise GUI, X11, game, input, or formal v6 arms.

## Observed outcome

| Script | Result | WSLc child wall time | Sampled child peak RSS |
|---|---:|---:|---:|
| v6 source/boundary | 3/3 pass | 89.484 ms | 13,044 KiB |
| v5 event-preservation | 4/4 pass | 97.557 ms | 12,364 KiB |
| v5 audit semantics | 3/3 pass | 85.044 ms | 16,888 KiB |
| v6 boundary audit | 3/3 pass | 103.609 ms | 15,628 KiB |
| v6 binding mutations | 6/6 rejected | 47.026 ms | 13,096 KiB |

Child RSS values are sampled at 1 ms and may miss shorter peaks; the cgroup high-water value is the primary memory observation. WSLc reported `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Readback showed `memory.swap.max=max`; therefore no swap cap is claimed. The configured memory ceiling itself was read back as 536,870,912 bytes.

Runtime: WSLc 3.0.1.0; Python 3.12.14; image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; kernel `6.18.40.1-microsoft-standard-WSL2-x86_64`; source read-only; network `none`.

No Docker Desktop Engine, v6 formal workflow, model/provider, game, GUI, GPU, physical input, or shared experimental slot was used. Preserve the underlying PR #6212 result unchanged; this replay only supplies the missing WSLc portability/resource-boundary observation.
