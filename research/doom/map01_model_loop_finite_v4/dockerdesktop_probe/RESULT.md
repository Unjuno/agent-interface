# Windows Docker Desktop construction result

Disposition: `PASS_CONSTRUCTION_SCOPED`; no OrbStack gate or formal v4 allocation is claimed. The concurrent OrbStack result posted on Issue #3880 remains the authoritative result for the preregistered OrbStack gate.

## H / T / D / C / U

- **H:** A measured host/container offset interval can support a conservative host-deadline translation for the existing runtime `Lease`; a delayed request with less than 20 s remaining can be refused before it reaches the container.
- **T:** One CPU-only run used 41 JSON-line request/response samples, then four lease cases via the same Docker stdio transport. It mounted the exact source `research/live_control/lease.py` read-only. No retry, game, model, or input action occurred.
- **D:** Independent raw-only audit: `PASS_CONSTRUCTION_SCOPED`, 41 clock rows, all four cases present, zero errors. The +25 s lease was accepted with 24.998815938 s remaining at container admission. The expired control produced `expired`; +31 s produced `rejected_horizon`; a 6 s delayed control had 18.9996452 s host time remaining and was rejected by the driver before sending any container request.
- **C:** Windows host Python 3.11.9; Docker Desktop 29.8.0, linux/amd64; image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; container Python 3.12 slim; `--network none`, read-only root, read-only checkout mount, 16 MiB `/tmp`. This is deliberately distinct from Issue #3880's pinned OrbStack linux/arm64 container and must not be pooled with it.
- **U:** The 1.399 s sample window cannot establish long-term drift, suspend/resume or container-recreation behavior. Offset interval max width was 610,305,440 ns, driven by a 610,309,000 ns max RTT; median RTT was 812,800 ns. No MAP01 runtime startup, model, task, or gameplay was exercised. This does not prove the offset remains valid for a later MAP01 container lifecycle.

## Frozen inputs and retained artifacts

- Base commit: `416851ab768c3c1f9add71ea3d63fe8b32fd95f3`.
- Driver SHA-256: `286bd8d595abd4cedd5e862ae72ad215378db0d6006102ca9ad33392c83e8c3f`.
- Worker SHA-256: `550bb7cfe7a389876a88aa5ffae9c0bedb1044fc36abf1c7611187c687a09fc1`.
- Independent auditor SHA-256 (summary/raw cross-check hardening): `b794404ebaeb6af7caf8293702a83fed43e989084e9b0ec80f41a4aa0cdc77b2`.
- Production Lease source SHA-256: `e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f`.
- Raw SHA-256: `171e4630d3dfa38677748eaf2300cb7974fe58d61c0e98f8cea96d412aaa6a4a`.
- Result SHA-256: `fabf7edf68e28a35c68d8b2e2465e5d4e63fb5a68888ab0098df0b3e5562dc22`.
- Independent audit SHA-256: `8a6da1e6ff7b2d2e17150d886cc0d3de2508c267cb0cb33e3e4a4b269b9dbb96`.

Evidence is retained at `research/doom/map01_model_loop_finite_v4/results/dockerdesktop-20260921-01/`. Reproduce using `dockerdesktop_probe/README.md`; the driver creates a fresh output directory and does not retry. The formal Issue #3880 allocation seed remains unconsumed by this run.
