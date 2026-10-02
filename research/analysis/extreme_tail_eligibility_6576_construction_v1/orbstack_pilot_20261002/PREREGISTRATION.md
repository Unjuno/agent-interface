# Issue #6576 single-case OrbStack pilot

Status: exploratory pilot; not formal T0 and not an input-release measurement.

## H / T / D / C / U

- **H:** On the preregistered stationary exponential synthetic reference, the eligibility gate will return `ELIGIBLE_REFERENCE`, and the raw-only independent auditor will reproduce all generated rows and reported statistics.
- **T:** In one isolated OrbStack Ubuntu 24.04 arm64 machine (2 vCPU, 4 GiB RAM), run the existing frozen candidate once and its independent raw-only auditor once on only `stationary_light_tail` (seed 65761001; 4000 train and 4000 holdout). Preserve complete raw rows and stdout/status artifacts.
- **D:** Pilot success requires candidate exit 0, auditor exit 0, exact frozen-case/raw reconstruction, eligible stationary reference, and nominal 1% exceedance included in the reported exact 95% interval for eligible fits. Otherwise retain failure without retry.
- **C:** This is one synthetic case on an isolated OrbStack Linux VM using its system Python, not the six-case formal T0 and not the pinned `python:3.12-slim` Docker image. It tests only this source/input/machine path.
- **U:** No physical input-release timing, real endpoint validity, other synthetic controls, TailID parity against CRAN/R, detector operating characteristics, safety deadline, production behavior, or worst-case bound is established.

Fixed case and source are inherited unchanged from the six-case T0 package at the recorded source HEAD. The one-case config is a pilot-only input; it does not alter the formal preregistration or consume the formal allocation. Candidate invocation: exactly once. Auditor invocation: exactly once only if candidate exits 0. Retries: zero.

Execution uses the named dedicated OrbStack machine only. No shared Docker Engine/container or other task's machine may be used. Record actual interpreter, architecture, CPU/memory/swap controls, machine identity, source/input hashes, raw output, auditor output, and exits. Any environment deviation from Docker is explicit and limits the result to this pilot.
