# Issue #5531 T5-E1 — hierarchical cut-depth sensitivity

## H / T / D / C / U

- **H:** A configured hierarchical failure-domain cut is only decision-correct
  when it matches the actual common-cause boundary. A cut that is too shallow
  should miss independent crash evidence; one that is too deep should produce
  false terminal-failure classifications.
- **T:** Enumerate every ordered pair of leaves in a synthetic 2×2×2
  site/rack/host hierarchy (8 leaves, 64 ordered pairs). Cross configured cut
  depths 1–3 with latent common-cause boundaries 1–3 (576 pair/cell evaluations).
  Compare the candidate's prefix cut with the declared finite-model oracle.
- **D:** `PASS_T5_EXPLORATORY_BOUNDARY_SENSITIVITY`: 0 errors on the three
  matched diagonal cells; mismatched cuts yield the exact false/missed counts in
  `raw-output.json`. The raw-only common-prefix histogram auditor reports PASS,
  and the copied-evidence corruption suite passes 3/3 tests (all nine matrix-row
  corruptions rejected, plus Docker-disclosure mutation rejected).
- **C:** The hierarchy is authored and perfectly known in this toy. A latent
  common-cause boundary is stipulated, not learned. Ordered pairs include
  identical leaf paths and symmetric duplicates. Counts are finite exhaustive
  counts, not probabilities or rates.
- **U:** This does not discover real failure domains, establish observer
  independence, model domain-map error, asynchronous timing, partitions,
  Byzantine witnesses, authority, runtime behavior, or production availability.
  It does not validate #5531's detector in deployment and is not an Issue #59
  MAP01 result.

## Execution and evidence

- GitHub `main` intake: `3befc5fb720e8d8aed3f6e6f3e6e881c42070f8e`.
- Evidence-package PR branch is based additively on refreshed `main`
  `241a0cac915df615f7f79b4ce2042b946ea7fbd7`; the experiment input/model
  itself is self-contained and has no repository source dependency.
- One host-only enumerator invocation: `python -B work/5531-cut-sensitivity-t5/run_experiment.py`.
- Python 3.12.10, Windows 11 x86_64. No network and no candidate invocation.
- Docker was available on the machine, but no named non-overlapping CPU/Docker
  lease existed in the #5085 queue; therefore no Docker command or image pull
  was made. This E1 probe is exploratory and host-only, not a replacement for a
  separately authorized container allocation.
- The first raw-only audit v1 ran once and passed. Its source and result are
  preserved. Auditor v2 adds a semantic SHA-256 check and independently passed
  against the unchanged raw. No candidate rerun occurred.
- `construction-tests.txt` preserves an initial test invocation failure caused
  by running the module from the wrong import context; the corrected invocation
  then passed all three tests. This is a command-context failure, not a changed
  experimental result.

## Result matrix

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

The result makes the hidden assumption in T4 explicit: a site-level cut is
correct only under a site-level latent common-cause model. A deeper or shallower
cut changes the tradeoff; this toy cannot tell us which boundary is true in an
actual deployment.
