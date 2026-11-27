# MAP01 V39 live threat guard A01

Allocation: `map01-v39-live-threat-guard-a01-20261009`  
Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)  
Frozen source: `origin/main` at `5f1761cec6b6b8cb4513aef6dbe0429d35569e97`  
Runtime: one dedicated OrbStack Ubuntu Noble arm64 VM; the original shared Docker daemon is not used.  
Fixture: `map01-threat-contact-v2`, seed `990619`, skill 1, MAP01, ViZDoom 1.3.0, exact Freedoom WAD hash in the fixture.

## H/T/D/C/U

**H — Hypothesis.** During a slow model answer, current typed health/ammo evidence can invalidate an authored cover policy; the V39 monitor should discard the dependent answer, cancel the matching live action, verify empty physical input, and then allow bounded recovery from a fresh observation. The run also measures whether feedback remains useful while the answer is pending and whether ammo/progress/terminal outcome remain acceptable.

**T — Treatment.** Run the frozen V39 controller once on the exact threat-contact fixture, using six maximum decisions, `gpt-5.6-luna` at low effort, seed 990619, and a 600-second episode timeout. Use the first-party Codex app-server through a host/VM JSONL relay with host-side local-image hash verification. No model prewarming, retries, manual gameplay, or alternate action path.

**D — Decision and measurements.** Retain all raw model protocol, controller events, typed HUD observations, runtime images, input-owner and release records, model usage, score, stdout/stderr, and hashes. Classify separately: actual health/ammo change; authored policy invalidation; matching cancel; per-key/empty release; stale-answer rejection; independently useful feedback; fresh bounded recovery; ammo/progress; and terminal state. Exposure is only established if the corresponding event chain is present in raw records. Compare descriptively with retained V38/V39 evidence only; no causal speed or general reliability claim.

**C — Controls.** Fixed source SHA, controller/helper hashes, ViZDoom/WAD/fixture hashes, model/effort, seed, map, skill, six-decision limit, timeout, schema, and no-retry stop rule. The allocation starts once and stops at six decisions, death, terminal, runtime/model failure, or 600 seconds. Preserve the first partial outcome. No in-place repair or rerun under this allocation ID.

**U — Uncertainty and scope.** One finite live episode cannot establish generality. HUD deltas are visible-state evidence, not enemy classification or causal damage attribution. Physical release evidence is limited to the current X11 owner contract; it does not prove hardware key state or application consumption. The runtime is a dedicated OrbStack VM, not a Docker container: nested Docker was denied by the VM's cgroup-device BPF boundary, and isolation was not weakened. If fixture load or controller startup reaches terminal before a decision, retain that result as a live STOP with zero model decisions.

## Stop and custody

At most six model boundaries; no retry. Freeze and hash the source and exact launch command before starting the model. The output path is `results-local/doom/map01-v39-live-threat-guard-a01-20261009/`. Preserve raw bytes and the initial result even on failure. The host relay forwards only bounded JSONL and verifies every `localImage` against a guest-written path receipt and host-side SHA-256 before forwarding it to the app-server.
