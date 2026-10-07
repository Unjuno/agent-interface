# T0 result — feasibility-aware estimability certificates (#7379)

**Disposition: `PASS_METHOD_SCOPED`.** The CPU-only finite method test completed on frozen main `13bab54ea6d91978247ecc1b70e5060db752367a`. The candidate and independent auditor each ran once, both exited 0, and there were no retries. The first main freeze stopped before candidate invocation and remains preserved separately at `feasibility_estimability_7379_t0_20261004/PRELAUNCH_STOP.md`.

The candidate enumerated **1,392 contrast/profile results**: 464 observed-support subsets across four finite feasibility sets, three target contrasts, and two explicit model profiles. The result classifications were:

| Classification | Results | Meaning |
|---|---:|---|
| `ESTIMABLE` | 3 | Both declared profiles identify the contrast from the support. |
| `NOT_ESTIMABLE` | 1,275 | Both profiles provide a separating null-space witness. |
| `UNRESOLVED_MODEL` | 114 | The two effect hierarchies disagree, so there is no model-independent classification. |

The compact profile produced 117 estimable and 1,275 non-estimable results; the saturated profile produced 3 estimable and 1,389 non-estimable. This confirms the hierarchy sensitivity is explicit rather than silently resolved in favor of the smaller model.

Representative controls behaved as preregistered. With all eight rows, the target contrast is estimable. In the `factor_A_fixed_low` feasibility set with support `[0, 2, 4, 6]`, the `main_A` contrast has no safe repair because the allowed set fixes factor A low. For support `[0, 1, 2]`, `interaction_AB` has a one-row minimum repair `[3]` under the compact model, while the saturated model requires five rows. With support `[0, 1, 2, 3, 4, 5, 6]`, `main_A` is estimable under the compact model but not under the saturated model, correctly producing `UNRESOLVED_MODEL`.

The exact executed auditor source is preserved byte-for-byte as `frozen_inputs/audit.executed.py.gz` (decompressed SHA-256 matches the freeze). A root-level whitespace-normalized presentation copy was created after the formal audit; it was not executed and did not replace the frozen bytes. The package-specific final whitespace scan passes. The earlier `git diff --check` did not inspect untracked files, so it did not catch trailing whitespace in the executed source; the exact source remains preserved and that limitation is recorded in `POSTRUN_FORMATTING.json`. The independent auditor uses fraction-free exact minor determinants for its rank oracle, then checks every row-space or null-space witness using exact rational arithmetic. It verified all 1,392 records, unique exhaustive support coverage, feasible and minimum-cardinality repair suggestions, and rejected all five mutations: infeasible arm, changed basis, invalid null witness, false estimable label, and nonminimal repair.

The raw candidate output is 553991 bytes (SHA-256 `9eb6f60b57f4eb514d1b70a2605dc46ff6b34d26ae32c685fbce7a65d3cddc52`). The auditor result is SHA-256 `427ae3cdfb8899707ffe68f571ce0a368aa6269906f86acf594db2f11ee7d517`. The frozen source bytes, spec, freeze, commands, raw logs, and exact run identities are retained in this directory and covered by `SHA256SUMS`. The post-run whitespace-only presentation copy is explicitly distinguished from the executed source.

This establishes finite arithmetic and certificate/audit behavior for the declared support sets and two model bases only. It does not establish causal identification, treatment consistency, randomization, power, external validity, or utility for real interface mechanisms. No outcomes were generated or imputed; no model, GUI, GPU, container, or live allocation was used. Any suggested safe augmentation is a design diagnostic, not authorization to run that configuration.
