# Fixed nonzero startup-overhead T4 — Issue #7327

## H / T / D / C / U

- **H:** For the three exact-rational fixtures, factor-2 homogeneous scaling preserves normalized observation traces. Leaving a nonzero startup delay fixed while scaling other time quantities changes the normalized stream and first hazard observation; a zero-startup control remains unchanged.
- **T:** Fresh allocation after T3's preserved zero-invocation main-advance STOP. Reuse the byte-frozen T3 candidate/auditor source without editing it; provide a new allocation ID/spec and new output path. Three fixtures: zero-startup negative control, nonzero-startup reachable hazard, nonzero-startup quiet control. One candidate invocation and one independent raw audit; four mutations; no retries.
- **D:** `PASS_FIXED_OVERHEAD_DISTINGUISHED` only if every homogeneous trace matches, the zero-startup fixed control matches, the homogeneous hazard reaction matches, the nonzero fixed-delay hazard reaction differs, and all four mutations are rejected.
- **C:** Synthetic exact-rational observation/event model only. Host CPython stdlib is used because OrbStack's current Engine API fails container inventory; no container resource-limit/speed claim.
- **U:** Whether the finite method fixture exposes a reachable failure of scale symmetry when a nonzero absolute startup overhead is not transformed.

## Frozen lineage and execution

Allocation `LOGICAL-TIME-SYMMETRY-7327-FIXED-OVERHEAD-T4-20261004-01`; frozen main is in `FREEZE.json`. T3's main-advance STOP and frozen source remain preserved in the sibling T3 path. T4 uses that exact candidate/auditor source as dependencies; its spec/output and allocation are distinct.

Run after prospective Issue #7327 registration:

```sh
python3 research/analysis/logical_time_symmetry_7327_fixed_overhead_t3_20261004/candidate.py research/analysis/logical_time_symmetry_7327_fixed_overhead_t4_20261004/spec.json research/analysis/logical_time_symmetry_7327_fixed_overhead_t4_20261004/output/raw.json
python3 research/analysis/logical_time_symmetry_7327_fixed_overhead_t3_20261004/audit.py research/analysis/logical_time_symmetry_7327_fixed_overhead_t4_20261004/spec.json research/analysis/logical_time_symmetry_7327_fixed_overhead_t4_20261004/output/raw.json research/analysis/logical_time_symmetry_7327_fixed_overhead_t4_20261004/output/audit.json
```

No GUI, game, model, GPU, physical input, or network is involved.
