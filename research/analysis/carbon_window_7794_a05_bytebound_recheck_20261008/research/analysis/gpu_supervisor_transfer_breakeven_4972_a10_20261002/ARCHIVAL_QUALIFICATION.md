# Allocation-10 construction archive qualification

Issue: [#5882](https://github.com/Unjuno/agent-interface/issues/5882)
Closed source PR: [#6362](https://github.com/Unjuno/agent-interface/pull/6362)
Original branch: `research/gpu-supervisor-transfer-breakeven-4972-a10-20261002`
Original head: `fbbf207e3cd6ee4e182d4885f5f3a459909b445e`

This archive preserves the exact A10 preparation package and its CPU-only
WSLc construction log. It does not promote the construction checks to a GPU
timing result. The historical package and SHA256SUMS are unchanged; the new
manifest records the actual recovered source bytes. Explicit SHA-256
verification of the original manifest found four mismatches: `audit.py`,
`dataset.json`, `FREEZE.json`, and `PREREGISTRATION.md`. The original expected
and recovered actual digests are retained here, not silently repaired.

| File | Historical expected SHA-256 | Recovered actual SHA-256 |
| --- | --- | --- |
| `audit.py` | `4f8c3586b42800d873d76b7fa6e04c0bee33778f99792e1267f0582adeb04948` | `61ce942aec45eddd2a974fcf555592e3b09b0a48ba76e8870a4cba4acbb34c6a` |
| `dataset.json` | `d73f6c5a83d4eed393e5cc3a2f5350d374fc5597ffcd403841d3f1966b885ecd` | `59e7335af94b8b504a3d6f9f3f0a3daebb23cbf61b8be8a74445b3db9f420987` |
| `FREEZE.json` | `f97debad7964ba67d4d95c804f87ceb4c27e913c47ae831c08df12c36d89ef5f` | `640d22b956a727654d65a2b571d42d4d4256136e738f5eb519716669c014d1e3` |
| `PREREGISTRATION.md` | `726b569b2404294025ea71742a39f2f32a4a6549cc7642234bc232e0f6b0516b` | `34419dfd47a07416c2cf7e27372b19dcae8ec308fe962f54ad2351d695ad1fc8` |

The recovered `audit.py` and `dataset.json` are opaque binary data (the
`audit.py` bytes fail Python UTF-8 parsing; `dataset.json` is not parseable as
JSON). They are preserved exactly as found and must not be represented as
locally executable source or valid dataset. Consequently the auditor mutation
test cannot be rerun from this recovered tree. The retained historical WSLc
log is independently hash-verified, but is historical construction evidence,
not a reproduction of the recovered bytes.

## H/T/D/C/U

- **H — Hypothesis:** transfer-inclusive CUDA may cross the frozen 20% latency
  improvement threshold at a tested batch size; otherwise CPU remains preferred
  for this synthetic hint workload. A10 did not test this hypothesis.
- **T — Treatment:** the historical preregistration defines the workload,
  sizes, repetitions, image/runtime and decision gates. The retained WSLc run
  was one CPU-only construction invocation using the pinned image with no GPU
  flag. It ran contract, unsafe-admission and synthetic auditor mutation
  controls only.
- **D — Decision:** archival status is `HOLD / STOP_BEFORE_CANDIDATE_EXPIRED_UNASSIGNED_WINDOW`.
  Candidate/CUDA/formal raw-auditor/retries = 0/0/0/0. No A10 crossover
  decision exists. Later allocation-12's `PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED`
  is distinct, already merged evidence and is not pooled here.
- **C — Controls:** the historical construction log reports contract 3/3, unsafe-admission
  3/3, clean synthetic auditor baseline, and rejection of 6 result plus 2
  source mutations. WSLc emitted a swap/cgroup warning; enforcement is not
  claimed because limits were not read back.
- **U — Uncertainty:** no formal candidate timing, CUDA call, or formal raw
  audit occurred; the requested GPU interval expired without an explicit
  coordinator assignment. The recovered four-file checksum discrepancy and
  opaque audit/data files prevent a clean source-level reconstruction.
  Historical construction evidence establishes package mechanics only, not
  performance, runtime safety, or product benefit.

Issue #5882 remains open. This archive requests no GPU interval and authorizes
no candidate, CUDA workload, auditor, or retry.
