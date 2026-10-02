# Issue #6576 OrbStack Docker pilot A02

Status: exploratory one-case pilot; not the formal six-case T0 and not a real input-release measurement. A01 was a separate STOP and will not be retried.

## H / T / D / C / U

- **H:** For a new fixed-seed stationary exponential synthetic reference, the existing fail-closed gate will report `ELIGIBLE_REFERENCE`, the estimated p99's held-out exceedance rate will be compatible with 1% under the preregistered exact 95% interval, and an independent raw-only auditor will reproduce the raw sample and candidate statistics.
- **T:** In a new isolated OrbStack Ubuntu 24.04 arm64 machine with its own Docker Engine, run the frozen candidate exactly once in the pinned `python:3.12-slim` image (`sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`), with network disabled, source read-only, and a unique writable output mount. One case only: `stationary_light_tail_a02`, seed 65761102, 4,000 train and 4,000 independent holdout rows. If candidate exits 0 and output exists, run the auditor exactly once in the same pinned image with read-only source and candidate output. Retries: zero.
- **D:** Pilot passes only when candidate and auditor exit 0, audit reports `PASS_METHOD_SCOPED PASS_RAW_ONLY cases=1 train=4000 holdout=4000`, gate eligibility is true, and the nominal 1% lies within the exact 95% interval for eligible gated p99. Any other outcome is retained without retry and is not a formal T0 disposition.
- **C:** This is one synthetic reference case using a source-backed but not CRAN/R-numerically-validated TailID Python equivalent. It does not test the five preregistered controls or the formal six-case aggregate rule.
- **U:** No physical release samples, real stationarity, causal dependence mechanism, unseen-mode coverage, safety deadline protection, production false-alarm rate, or worst-case bound is tested.

This successor pilot uses a new seed and a new allocation. It does not repeat or overwrite A01 and does not consume the formal allocation `EXTREME-TAIL-ELIGIBILITY-6576-T0-ORB-20261002-01`. Record exact source/input/image/machine identity, effective CPU/memory/swap controls, raw candidate output, exits, auditor output, and all hashes. If the isolated VM Docker daemon, image identity, writable output mount, or resource enforcement cannot be verified before candidate invocation, stop before candidate and preserve the setup STOP.
