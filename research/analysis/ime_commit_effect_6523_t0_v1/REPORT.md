# Issue #6523 synthetic IME phase/effect T0 — result

## Outcome

`PASS_METHOD_SCOPED`; the preregistered finite synthetic contract was reconstructed for all 12 traces × 4 routes (48 rows), and all six frozen output-corruption controls were detected. This is a method-fixture result only, not evidence about actual IME, browser, application, or user behavior.

The candidate completed once (exit 0); the independent auditor completed once (exit 0). Candidate and audit machine-readable outputs are retained in `formal_01_20261002/output/`. Exact source, raw, and auditor-output SHA-256 digests are in `SHA256SUMS.txt`; container commands, WSLc image digest, resource request, and limitations are retained alongside them.

## Frozen route comparison

| Route | Excess submits vs. authored trace oracle | Traces with excess | False completion claims |
|---|---:|---|---:|
| `RAW_ENTER` | 5 | composition-unavailable; delayed-value-after-compositionend; ime-cancel; ime-confirm-then-submit; literal-enter-without-submit | 0 |
| `SYMBOLIC_ONLY` | 1 | delayed-value-after-compositionend | 0 |
| `NATIVE_FILL` | 1 | delayed-value-after-compositionend | 0 |
| `PHASE_AWARE` | 0 | none | 0 |

The narrow synthetic contrast supports `H_SUPPORTED_METHOD_ONLY`: phase-aware interpretation avoided the authored premature-submit cases, whereas raw Enter did not. It does not establish that native fill or any key route behaves this way in a real runtime. A single-line native-fill success control and Latin-submit control passed. Missing/mismatched effects did not yield completion claims. Focus generation prevented the stale-target events in the phase-aware route.

## Reproducibility and limits

- Candidate and auditor were each run once, in separate WSLc containers, using the pinned cached `python` image digest, `--network none`, `--cpus 1`, and requested `--memory 512M`; no GPU, GUI, IME, model, external effect, Docker, or Podman was used.
- WSLc warned that swap-limit cgroup support is unavailable; the warning says memory is limited without swap. This report makes no stronger resource-isolation claim.
- The fixtures are authored semantics, not observed event logs. Auditor reconstruction is algorithmically separate but shares the frozen route contract; mutation controls demonstrate specified corruption sensitivity, not general auditor correctness.
- The repository-level analysis index checker could not be meaningfully run from this sparse checkout: sibling result directories were absent. The separate existing index regression suite had 2 failures (`test_duplicate_entry_still_fails`, `test_unsorted_entries_still_fail`) and 4 passes; no unrelated checker code or generated index was changed.
- H/T/D/C/U, construction tests, exact commands, and freeze metadata are preserved in this directory.
- T1 remains untested. It requires a separate allocation and preregistration on an IME-capable GUI host with independent application-save/server-effect evidence; this T0 is not a basis to claim product efficacy.
