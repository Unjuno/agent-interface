# Windows Docker Desktop construction result

Disposition: `HOLD_CONTAINER_EXIT_UNRECORDED`; no OrbStack gate or formal v4 allocation is claimed. The semantic clock/lease rows independently reconstruct with no errors, but the first driver did not retain the Docker CLI child exit code. The initial `audit.json` PASS is preserved as a historical limited raw-row check; the follow-up audit records this overall hold. The concurrent OrbStack result posted on Issue #3880 remains the authoritative result for the preregistered OrbStack gate.

## H / T / D / C / U

- **H:** A measured host/container offset interval can support a conservative host-deadline translation for the existing runtime `Lease`; a delayed request with less than 20 s remaining can be refused before it reaches the container.
- **T:** One CPU-only run used 41 JSON-line request/response samples, then four lease cases via the same Docker stdio transport. It mounted the exact source `research/live_control/lease.py` read-only. No retry, game, model, or input action occurred.
- **D:** Follow-up independent audit: semantic disposition `PASS_CONTROLS_AND_CLOCKS_SCOPED`, 41 clock rows, all four cases present, zero semantic errors; overall disposition `HOLD_CONTAINER_EXIT_UNRECORDED` because the original result lacks the child exit code. The +25 s lease was accepted with 24.998815938 s remaining at container admission. The expired control produced `expired`; +31 s produced `rejected_horizon`; a 6 s delayed control had 18.9996452 s host time remaining and was rejected by the driver before sending any container request.
- **C:** Windows host Python 3.11.9; Docker Desktop 29.8.0, linux/amd64; image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; container Python 3.12 slim; `--network none`, read-only root, read-only checkout mount, 16 MiB `/tmp`. This is deliberately distinct from Issue #3880's pinned OrbStack linux/arm64 container and must not be pooled with it.
- **U:** The 1.399 s sample window cannot establish long-term drift, suspend/resume or container-recreation behavior. Offset interval max width was 610,305,440 ns, driven by a 610,309,000 ns max RTT; median RTT was 812,800 ns. No MAP01 runtime startup, model, task, or gameplay was exercised. This does not prove the offset remains valid for a later MAP01 container lifecycle.

## Frozen inputs and retained artifacts

- Base commit: `416851ab768c3c1f9add71ea3d63fe8b32fd95f3`.
- Original run driver SHA-256 (did not record child exit): `286bd8d595abd4cedd5e862ae72ad215378db0d6006102ca9ad33392c83e8c3f`.
- Hardened reproduction driver SHA-256 (5 s response timeout; checks exit code): `2e10c16eea93003b5cf92a8eb98e6180d98c65b93dc1ecbef76e75c2137f8da2`.
- Worker SHA-256: `550bb7cfe7a389876a88aa5ffae9c0bedb1044fc36abf1c7611187c687a09fc1`.
- Follow-up auditor SHA-256 (duplicate, raw/summary and child-exit checks): `6d048ec727662d3f2bbf6d0b26c369ba3309a511e80f26f9913929cd60c2f4a6`.
- Auditor corruption tests SHA-256: `f509837a6720101301b426cdab86fccc793a3e7ff69ae249e679c24439ddeab4` (4/4 pass: missing exit hold, duplicate control rejection, control-summary mismatch rejection, clock-summary mismatch rejection).
- Production Lease source SHA-256: `e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f`.
- Raw SHA-256: `171e4630d3dfa38677748eaf2300cb7974fe58d61c0e98f8cea96d412aaa6a4a`.
- Result SHA-256: `fabf7edf68e28a35c68d8b2e2465e5d4e63fb5a68888ab0098df0b3e5562dc22`.
- Independent audit SHA-256: `8a6da1e6ff7b2d2e17150d886cc0d3de2508c267cb0cb33e3e4a4b269b9dbb96`.
- Follow-up audit SHA-256: `0aa99b140aafe1a4fd426bd7d4d456f5573d3597068898e0947403fbcbfe2a97` (`HOLD_CONTAINER_EXIT_UNRECORDED`; semantic controls still pass).

Evidence is retained at `research/doom/map01_model_loop_finite_v4/results/dockerdesktop-20260921-01/`. Reproduce using `dockerdesktop_probe/README.md`; the driver creates a fresh output directory and does not retry. The formal Issue #3880 allocation seed remains unconsumed by this run.
