# Issue #8004 — oracle-separated method construction A02

**Disposition: PASS_CONSTRUCTION_ONLY (exploratory development run); full
Issue #8004 T0: HOLD.** Candidate input and sealed truth oracle are separate
files/process inputs. The independent auditor reconstructs a finite 2×2 grid,
six latent opportunities and three-channel truth histories, and separately
reports false/missed links, false merges/splits, censoring and missing telemetry.
The exact inputs were iterated during unit-test development, so this is not a
preregistered formal T0; see `PREREGISTRATION_DEVIATION.md` and
`DEVELOPMENT_HISTORY.md`.

## H / T / D / C / U

- **H (A02 prerequisite):** Independent ascertainment accounting must not need
  candidate access to latent truth, and should retain common-blind-spot,
  censored and telemetry-missing opportunities in distinct denominator states.
- **T:** Candidate reads `observations.json` only; it enumerates two authored
  segmentation alternatives × two anonymous linkage alternatives. Separate
  auditor reads `oracle.json`, reconstructs all 4 assignments, all raw-record
  partitions, per-opportunity channel histories and errors. Eight mutation/API
  tests include oracle-field leakage, forced consensus, deleted plausible link,
  raw-record duplication/split counting, dropped censored opportunity, false
  link and unsupported zero-unseen labeling.
- **D:** A02 construction passes if all four assignments and five raw records
  are conserved, all six oracle opportunities are accounted for, masks keep
  censoring/missing distinct from observed zero, and independent reconstruction
  plus mutations pass. This gate passed in the retained exploratory run.
- **C:** Assignment alternatives are authored and intentionally small. The
  candidate returns observed equivalence classes and `UNIDENTIFIED`; it does
  not estimate an unseen population or validate alternative weights.
- **U:** Six authored opportunities, three channels, five observed records,
  two segmentation choices and two linkage choices. No natural traces,
  calibrated detector/linker errors, causal channel-dependence model, posterior,
  production rate or safety conclusion. #8004's joint-only H gate is not
  demonstrated: segmentation alone changes the candidate histogram in this
  fixture, while crossed linkage does not change that histogram.

## Result

- Candidate: 4 assignments; disposition `UNIDENTIFIED`.
- Independent auditor: `ok=true`, 4/4 assignments, 6/6 latent opportunities,
  4 fully observed opportunities, 1 true all-channel-zero opportunity; one
  right-censored and one missing-interval opportunity represented separately.
- Oracle capture-history counts, channel order runtime/watcher/verifier:
  `110:1`, `101:1`, `010:1`, `000:1`, `00?:1`, `0?0:1`.
- Crossed linkage creates 2 false links in either segmentation. Split+crossed
  misses both multichannel opportunities; merged alternatives create false
  merges. The auditor does not pool these error classes.
- Tests: 8/8 normal and 8/8 optimized Python; candidate/auditor commands,
  outputs, errors and hashes are retained.

This is a prerequisite method-construction result only. It does not satisfy
Issue #8004's `PASS_METHOD_SCOPED` or `H_PASS_SCOPED`; the full T0 remains HOLD.

## Execution environment and reproduction

macOS 27.0.1, Python 3.14.5, standard library only. OrbStack image listing
stopped on a containerd content blob (`operation not supported`). Candidate and
auditor therefore ran on host as exploratory work; no image pull, container
launch, prune, VM start, daemon mutation, model, GUI, network or live allocation
was used.

## Parallel-work disposition

After this exploratory run, GitHub Issue #8004 received a separate preregistered
formal T0 A02 allocation, frozen on branch
`research/8004-joint-unitization-linkage-t0-a02-20261005` and reported in PR
[#8020](https://github.com/Unjuno/agent-interface/pull/8020). That independent
allocation exercises the issue's fuller four-channel joint-only H gate and
reports `PASS_METHOD_SCOPED` / `H_PASS_SCOPED`. This exploratory package is not
that allocation, was not reused in it, and must not be counted as a second
independent confirmation. Prefer PR #8020 as the issue-level T0 result; retain
this package only as separately scoped development/preflight history.

```sh
python3 -m unittest -v test_method
python3 -O -m unittest -v test_method
python3 candidate.py --observations observations.json --output run_candidate.json
python3 auditor.py --observations observations.json --oracle oracle.json --candidate run_candidate.json --output run_audit.json
python3 -m py_compile candidate.py auditor.py test_method.py
```
