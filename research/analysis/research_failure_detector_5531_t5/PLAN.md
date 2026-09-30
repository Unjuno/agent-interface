# Issue #5531 T5-E1 — exploratory cut-depth sensitivity plan

This is an exploratory finite-model probe, not a preregistered formal or live
allocation. The core T4 site-cut experiment is not rerun. The new question is
whether its classification depends on the assumed hierarchy cut.

## H / T / D / C / U

- **H:** Classification errors arise when configured cut depth differs from a
  stipulated latent common-cause boundary: a shallower cut misses some
  independent crash evidence and a deeper cut yields false `FAILED` states.
- **T:** Enumerate the 8 leaves of a 2×2×2 site/rack/host hierarchy; evaluate all
  64 ordered leaf pairs across cuts 1–3 and latent boundaries 1–3.
- **D:** Report exact false- and missed-`FAILED` counts for all nine cells. The
  expected structural property is zero error when depths match and nonzero
  error for at least one mismatched cell on each side. This is a descriptive
  criterion, not a statistical threshold.
- **C:** Leaf identity and latent common-cause boundary are perfectly stipulated
  by the synthetic generator; this is not domain discovery.
- **U:** No claim about real observer independence, timing, availability,
  authority, or runtime behavior.

## Stop / execution boundary

No network or candidate implementation call is needed. The host-only finite
enumeration is small and deterministic. Docker was deliberately not invoked:
the shared #5085 CPU/Docker queue had no exact non-overlapping lease for this
allocation. The result must remain labeled exploratory and host-only. Preserve
raw output, both audit versions, test-command failure, and all hashes. Do not
upgrade this result into validation of the production failure detector.

The enumerator was recorded after execution for reproducibility; this document
does not claim a pre-run source freeze or preregistration. Exact local commands
and outcomes are in `execution.json` and `construction-tests.txt`.
