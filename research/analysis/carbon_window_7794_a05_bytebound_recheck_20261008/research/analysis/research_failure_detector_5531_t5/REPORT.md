# Issue #5531 T5-E1 — hierarchical cut-depth sensitivity

## H / T / D / C / U

- **H:** A configured hierarchical failure-domain cut is decision-correct only
  when it matches the actual common-cause boundary. A cut that is too shallow
  misses independent crash evidence; one that is too deep can produce false
  terminal-failure classifications.
- **T:** Enumerate all ordered pairs of the eight leaves in a synthetic 2×2×2
  site/rack/host hierarchy (64 ordered pairs). Cross cut depths 1–3 with latent
  common-cause boundaries 1–3 (576 pair/cell evaluations). Compare a prefix cut
  to the finite-model oracle.
- **D:** `PASS_T5_EXPLORATORY_BOUNDARY_SENSITIVITY`: all three matched cells
  have zero false/missed `FAILED`. Mismatched cells produce the exact counts
  below. Raw-only independent common-prefix histogram auditors v1 and v2 both
  pass. Construction/mutation tests pass 3/3 (nine row corruptions and one
  Docker-disclosure corruption rejected).
- **C:** The hierarchy and latent boundary are authored and perfectly known in
  this toy. The latent boundary is stipulated, not learned. Ordered pairs
  include identical paths and symmetric duplicates. These are finite counts,
  not probabilities or rates.
- **U:** Does not discover real failure domains, establish observer
  independence, model mapping error, asynchronous timing, partitions,
  Byzantine witnesses, authority, runtime behavior, or production availability.
  Does not validate #5531's detector in deployment or resolve Issue #59 MAP01.

## Exact outcome matrix

| Configured cut | Latent boundary | False `FAILED` | Missed `FAILED` |
|---:|---:|---:|---:|
| 1 | 1 | 0 | 0 |
| 1 | 2 | 0 | 16 |
| 1 | 3 | 0 | 24 |
| 2 | 1 | 16 | 0 |
| 2 | 2 | 0 | 0 |
| 2 | 3 | 0 | 8 |
| 3 | 1 | 24 | 0 |
| 3 | 2 | 8 | 0 |
| 3 | 3 | 0 | 0 |

This makes T4's hidden assumption explicit: a site-level cut is correct only
under a site-level latent common-cause model. This toy cannot identify which
boundary is true in deployment.

## Execution provenance

One host-only enumerator invocation, CPython 3.12.10 / Windows 11 x86_64; no
network, Docker, or candidate implementation invocation. Docker was not started
because #5085 had no exact non-overlapping CPU/Docker lease. This was exploratory
and not preregistered; the recorded runner supports reproduction but was not
frozen before execution. The intake main was
`3befc5fb720e8d8aed3f6e6f3e6e881c42070f8e`; the additive PR branch uses refreshed
main ancestry. See `PLAN.md`, `execution.json`, `construction-tests.txt`, both
audit result files, raw output, and `SHA256SUMS.txt` for details.
