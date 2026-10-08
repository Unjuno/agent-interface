# A07 preregistration — fresh successor after A06 output-permission STOP

## H / T / D / C / U

- **H:** On fresh stationary exponential fixtures, varying `ismev::gpd.fit` starts/methods can produce material fit/objective differences near a finite-sample likelihood boundary; if R fits are stable but the pre-A06 Python port diverges, follow-up should focus on the Python optimizer/termination behavior rather than an unstable R reference.
- **T:** Generate six new `n=400` exponential samples with R 4.4.3 and seeds 65769937–65769942. Match A05 base-fit construction: type-7 0.90 threshold, remove the two largest observations. One R candidate invocation runs default Nelder–Mead plus five fixed starts/method variants. One Python candidate invocation applies the frozen pre-A07 TailID-equivalent port once per sample. One independent Python auditor recomputes thresholds, candidate masks and every reported likelihood from frozen samples. Candidate invocations R=1/Python=1; auditor=1 only after both candidates exit 0; retries=0.
- **D:** `R_OPTIMIZER_SENSITIVE` if any fixture's converged R fits have relative scale range / median >0.001, shape range >0.001, or negative-log-likelihood range >1e-6. Otherwise `R_FITS_STABLE_AT_GATE`. Separately compare default R with Python using relative scale <=0.001 and absolute shape <=0.001. Audit verifies R likelihoods within 2e-5 and all sample hashes. Invalid raw receipts make the audit invalid, not a scientific result.
- **C:** Six fresh synthetic fixtures test only numerical optimizer sensitivity under the named construction. This does not estimate tail risk, compare statistical quality, validate the overall #6576 gate, or establish operational behavior.
- **U:** No formal six-case #6576 T0, physical input-release timing, key-up, GUI, safety, worst-case, production or broad package-equivalence claim.

## Frozen execution protocol

Same dedicated #6576 OrbStack VM/private Docker Engine and image digests as A06. A06's UID 1000 output-mount failure is not retried. Before candidate freeze, two separate preflight containers (one per frozen image) must successfully write and read a sentinel on fresh disposable output mounts using the default container root identity. Candidate containers then use distinct fresh output directories and default root identity, network disabled, read-only root/source/input, and 1 CPU / 2 GiB memory / 0 swap. `docker inspect` must confirm both mounts and limits before start. Candidate R and Python are started exactly once each. Auditor runs exactly once only if both exit 0. Any failure is preserved; no in-place repair or rerun.

The fixed R variants are: default Nelder–Mead; Nelder–Mead starts `(1,0)`, `(2,-0.75)`, `(0.5,-1.25)`; default-start BFGS; BFGS start `(1,0)`. No adaptive starts, selective fixture exclusion, or post-result tolerance changes.
