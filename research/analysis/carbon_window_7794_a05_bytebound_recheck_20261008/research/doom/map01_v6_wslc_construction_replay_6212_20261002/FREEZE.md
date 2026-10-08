# WSLc construction-replay freeze — PR #6212 successor

- Allocation ID: `MAP01-V6-CONSTRUCTION-WSLC-20261002-01`.
- Purpose: directly test the migration question left open by PR #6212: do its exact five deterministic construction scripts run unchanged in WSLc, where Docker Desktop's Engine was unavailable? This is portability/resource-boundary evidence only, not a new recovery experiment.
- Source commit: `14b81dd1f6853623a694266b98538f812847257a`.
- Source mode: detached, read-only bind mount from a sparse checkout; expected Git blob identities are listed below.
- Scripts, each run in a separate CPython subprocess exactly once, in the PR's order:
  1. `research/doom/test_map01_recovery_cover_mechanism_v6.py`
  2. `research/doom/test_map01_recovery_cover_mechanism_v5.py`
  3. `research/doom/test_audit_map01_recovery_cover_mechanism_v5.py`
  4. `research/doom/test_audit_map01_recovery_cover_mechanism_v6.py`
  5. `research/doom/test_audit_map01_recovery_cover_mechanism_v6_bound.py`
- **H:** The same five tests will pass unchanged under WSLc's pinned Python runtime with bounded CPU/memory and network disabled; measured cgroup memory will remain below the configured 512 MiB ceiling.
- **T:** One container run, all five scripts in separate child processes, no retries. Capture exact stdout/exit codes, wall time and sampled per-child RSS; read actual `cpu.max`, `memory.max`, `memory.swap.max`, `memory.peak`, and `memory.current` inside the container. Compare logical outputs only with the Windows/WSL expected results recorded in PR #6212.
- **D:** `PASS_WSLC_CONSTRUCTION_PORTABILITY_SCOPED` only if all five exact outputs and counts match PR #6212, every child exits 0, cgroup reports 2 CPU / 536870912-byte memory cap, and peak usage is below the cap. Otherwise retain FAIL/STOP/HOLD verbatim. No speedup or cross-environment memory-reduction claim because PR #6212 did not record comparable timing/RSS.
- **C:** These are deterministic construction tests with fakes, not formal/live arms. The scripts may be insensitive to platform-specific filesystem, GUI, or game behavior.
- **U:** No evidence of reduced iteration latency versus Windows/WSL/Docker, no measured memory comparison, no swap-limit guarantee if the kernel lacks support, no bounded-recovery efficacy or runtime/game/GUI/input result. Does not consume or authorize the v6 formal allocation.
- WSLc image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; options `--network none --cpus 2 --memory 512M`; source mount read-only; WSLc 3.0.1.0.
- No formal v6 workflow, Docker Desktop operation, model/provider, game, GUI, GPU, physical input, or shared allocation.

## Frozen Git blobs

- v6 source/boundary test: `8bc6190ebfd06ad55feca3ed1c09e0f104f37a6b`
- v5 event preservation test: `96e5f0a7cee5623fbde8a3a18b3d965f09a9a8e7`
- v5 audit decision test: `61b52279435cdeff329561b0c0723864486af0ef`
- v6 boundary audit test: `acb08cac77d3dcc82a2535018d24b32308545d56`
- v6 binding mutation test: `c160c6d03272de4c6521b3fdd3676df2ef16cdc1`
- v6 runner source: `10344582ffa2ce339bc48dd8d680512a71f4eddc`
- v5 runner source: `f1b5488f6a039c60afc2af5c7a4e86de8773ecd0`
- v5 auditor source: `609fd1a9e655e03a3e595d6823a6a4f793e397aa`
- v6 auditor source: `e3c34caad26a5a7e17d2464c945b74f747b75d4b`
- v6 binding auditor source: `1fb5143086784e86565057c3d1e5bd9ca6d05b7e`
