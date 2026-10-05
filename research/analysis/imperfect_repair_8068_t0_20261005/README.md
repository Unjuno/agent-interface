# Issue #8068 T0 — imperfect-repair method fixture

## H / T / D / C / U

**H (method hypothesis).** A small, independently enumerated fixture can distinguish perfect renewal, minimal repair, and an intermediate history-conditioned repair transformation while preserving exposure, censoring, and required task effects; its auditor rejects the predeclared contamination mutations.

**T.** Deterministic seven-cycle, no-model/no-GUI fixture. Fault class is fixed; pre-repair latent ages are 0 or 2; exposure counts are unequal (total 12). Repair operators map age to 0 (perfect), unchanged (minimal), or `max(0, age - 1)` (intermediate). An independent oracle reconstructs post-recovery health and recurrence from frozen uniforms and risk `0.1 + 0.2 * post_age`. One cycle is right-censored. Calibration IDs `{p0,p1,m0,m1}` and evaluation IDs `{i0,i1,c0}` are disjoint and frozen. Required effect receipts must survive every repair.

**D.** `METHOD_PASS_SCOPED`: 7/7 focused tests passed under normal Python and `-O`; AST parsing passed 3/3. The independent oracle distinguishes the three transformations at pre-age 2 (post-ages 0, 2, 1) and rejects evaluation-outcome leakage, exposure alteration, fault-class relabeling, erased required effects, fabricated censored outcomes, and recurrence-oracle disagreement. No hypothesis about actual repair effectiveness was tested.

**C.** Perfect-renewal, minimal-repair, and intermediate-repair transition rules are enumerated directly. This is a methods fixture, not a predictive model comparison against an empirically fitted history-free baseline.

**U.** All rows and latent ages are authored. The probabilities/uniforms are illustrative deterministic inputs, not empirical rates. No causal recovery effect, calibrated uncertainty, GUI/application behavior, runtime policy, retry permission, task benefit, or safety result follows. T1 retained-trace eligibility and separately authorized T2 are not run.

## Execution provenance and outcomes

- Repository base: `7a9398add78d9095e5a85a60d324513fc3c2a1e3` (GitHub `main` at intake, 2026-10-05).
- Branch: `research/8068-imperfect-repair-t0-20261005`; additive path only.
- Runtime: WSLc `3.0.1.0`, image `agent-interface/native-suite-wslc-a08:20261004`, image ID `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`, Python 3.12.14; network disabled; read-only bind; 1 CPU and 512 MiB requested.
- Host warning on every invocation: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Therefore hard memory/swap enforcement is not established.
- Initial run: 5/6 passed, one fixture assertion failed because expected exposure total was mistakenly written as 13; frozen rows sum to 12. Candidate/oracle tests otherwise passed. The failed first result is retained here; after correcting only that expected total and adding the predeclared outcome-leakage check, final runs were 7/7 normal and 7/7 under `-O`.
- AST check: 3/3 source files parsed. Candidate summary: exposure total 12; cycle `c0` remains censored/unknown. No retries of a consumed allocation were involved; this is a repeatable deterministic method construction.

## Reproduction

From the experiment directory, with WSLc and the pinned local image available:

```powershell
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 -m unittest -v
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 -O -m unittest -v
```

The image's default entrypoint is repository-specific; `--entrypoint python` is required for this isolated fixture.
