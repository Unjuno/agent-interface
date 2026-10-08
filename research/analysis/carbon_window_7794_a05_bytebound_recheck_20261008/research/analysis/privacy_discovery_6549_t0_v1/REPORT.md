# Issue #6549 T0 — finite supported-class privacy/discovery frontier

## Disposition

`PASS_METHOD_SCOPED` for the deterministic synthetic accounting fixture only. No private mechanism was implemented or certified; the bounded-noise arm is explicitly an uncertified sensitivity illustration. No real telemetry, GUI, model, network upload, or field utility result.

## H / T / D / C / U

- **H:** The exact-label singleton limitation follows analytically from the Issue's stated user-level DP premise; for the tested synthetic comparator, a coarse predeclared merged category can retain support while singleton, split-taxonomy, correlated, duplicate, and threshold-suppressed cases must remain UNKNOWN.
- **T:** One CPU-only, standard-library finite allocation, frozen on main `afea9a530cafd7af529df4c9e59f36b816bca24f`. Eight authored cohort histograms crossed with deterministic subtractive sensitivity offsets `eta=0,1,2`: 24 rows. Candidate and separate raw-only auditor each ran once; retries 0.
- **D:** 24/24 candidate rows independently reconstructed; zero errors; six construction tests passed; four audit corruption controls rejected. Exact upper-bound arm is labeled NON_PRIVATE; no DP guarantee is attributed to the noise display; all suppression is UNKNOWN.
- **C:** Small synthetic cohorts with authored counts and fixed taxonomy mapping only. `eta` is not sampled DP noise, and findings do not estimate an actual system's privacy or discovery rates.
- **U:** No composition, adaptive taxonomy, realistic dependence, malicious-client model beyond the duplicate fixture, side-channel, severity utility, or consent/participation model. No real cohort size or risk rate follows.

## Execution and independent result

WSLc was unavailable in the macOS host (`wslc.exe` not found). The OrbStack Docker engine did not answer a read-only `docker ps` within the bounded check; no container was started or shared container touched. Because this deterministic standard-library experiment needs no container-only behavior and the frozen allocation permits local CPU if WSLc is unavailable, formal execution used host CPython 3.14.5, arm64, offline/local files only. This is a host run, not a container result.

The independent audit reconstructed 24/24 rows with `errors=[]`. Under the **assumed** `(epsilon=1, delta=0)` user-level DP premise, at false-report probability `alpha=0`, the singleton discovery upper bound is 0; demanding `beta=0.9` requires `alpha >= 0.331091497...`. This is the conditional inequality already stated in #6549, not verification of a mechanism.

The deterministic noise display illustrates the finite sensitivity tradeoff: a supported class with count 2 is discovered at eta 0 and suppressed as UNKNOWN at eta 1/2; a predeclared merged class with support 4 remains discovered at all three offsets. A taxonomy split with unknown allocation remains UNKNOWN. Correlated and duplicate-client cohorts remain UNKNOWN for every offset. The no-failure control is typed distinctly and does not prove population absence.

Construction tests: 6/6 passed. Formal candidate: exit 0, 24 rows. Separate auditor: exit 0, 24 reconstructed, zero errors. Raw and audit hashes are retained in `results/allocation-01/SHA256SUMS`; the raw candidate SHA-256 is `df20259dc7bbf1f2993a1d7d02a7821d3f62e08c12ee112112cc55f08944d9cb`.

## Scope and next boundary

The analytical singleton bound is not re-simulated as if Monte Carlo could override it. The remaining synthetic comparison only exposes finite supported-class/taxonomy/suppression accounting. Any future claim about user-level DP requires a concrete mechanism, explicit adjacency and composition accounting plus independent privacy review. Real collection still requires explicit consent and governance; no telemetry authority is created here.
