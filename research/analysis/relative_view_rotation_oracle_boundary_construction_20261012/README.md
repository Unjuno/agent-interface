# Issue #8636 — oracle boundary construction patch

**Disposition: construction-only PASS, scoped to the arm boundary.** This is a
prospective patch and regression test for a future allocation. It does not edit
the frozen A04 package, rerun A04, audit A04's retained raw, or change A04's
`HOLD_UNCERTAIN` result.

## Finding and proposed behavior

The first A04 audit mismatch is `feature_loss-30090-viewstate_oracle`, step 0.
The runner invokes image detection before selecting the arm, so the near-singular
image causes the privileged ViewState oracle to yield. The independent auditor
also tries to detect points before selecting its arm; simply bypassing detection
in the runner would still fail the auditor. The patch moves both control and
audit feature handling behind an arm boundary:

- `viewstate_oracle` computes its bounded action from the scorer-only pose and
  emits `points=null` and `feature_vector=null` without image detection.
- Image arms keep the existing detector and still must yield when a required
  landmark is missing or ambiguous.
- The raw-only auditor skips image detection only for the oracle arm. It still
  independently reconstructs the oracle action/status, while image-arm rows
  retain the existing invalid-image checks.

The patch applicator is in [`apply_oracle_boundary_patch.py`](apply_oracle_boundary_patch.py).
It refuses to operate outside a system temporary directory and checks the
three frozen source hashes before changing its temporary copy. The regression tests are in
[`test_oracle_boundary.py`](test_oracle_boundary.py).

## H / T / D / C / U

- **H:** On the frozen synthetic `near_singular` seed 30090 frame, the oracle
  action and its independent audit decision do not depend on image detection;
  the image controller still fails closed on that same frame.
- **T:** Apply the patch to a temporary extraction of A04 frozen source commit
  `2f15e4f9a68cea4b9e47940b8f9b468ba5dd07cf`. Run the four new construction
  tests and the 13 existing construction regressions other than the immutable
  source-manifest assertion, in normal and optimized Python. The focused test
  first failed against the unmodified source because `control_step` and
  `audit_image_points` did not exist.
- **D:** PASS only if all four new tests and all 13 applicable existing
  construction regressions pass in both modes, including image-arm abstention;
  otherwise FAIL. No formal candidate or full auditor invocation is part of
  this construction check.
- **C:** An oracle that requires image-derived evidence is not an independent
  upper-reference arm. Alternatively, one could redefine the oracle to yield
  on image failures, but that would make its reference behavior depend on the
  perception mechanism under comparison and would not resolve the stated
  A04 protocol semantics.
- **U:** This does not validate all 360 trials, raw custody, scientific
  hypothesis thresholds, real GUI behavior, OS input/release, runtime safety,
  latency, model behavior, or product benefit. A future formal allocation must
  separately freeze the corrected runner, auditor, source hashes and gates.

## Verification record

Environment: Windows host, CPython 3.11; deterministic CPU-only construction
checks. No WSLc/container, GUI, game, model, OS input, formal candidate, or full
auditor run was invoked. WSLc was excluded because the A04 protocol names no
container runtime and the shared WSLc owner is unresolved in the current #7924
record.

Results on the patched temporary source tree:

| Check | Normal | `-O` |
|---|---:|---:|
| New oracle-boundary regressions | 4/4 PASS | 4/4 PASS |
| Applicable existing A04 construction regressions | 13/13 PASS | 13/13 PASS |

The one omitted existing construction test checks the original source hashes;
it is inapplicable to a patched copy and was not treated as passing. The patch
was applied successfully by the guarded patch applicator to a fresh archive of
the frozen source commit.
Reproduce with:

```powershell
python -B research/analysis/relative_view_rotation_oracle_boundary_construction_20261012/verify_construction.py
```

When unrelated repository-wide discovery imports the test module without
`A04_SOURCE_DIR`, its four cases skip cleanly. The verifier sets that variable
only for the temporary pinned source tree.

The A04 source hashes used for the temporary tree were:

| File | SHA-256 |
|---|---|
| `candidate.py` | `e058cdc69700b5cb08bbda13cb90c83caca36e238edcddbd9fde5cfced76d1a4` |
| `runner.py` | `a301dcbc4650c7327d9ef31c11ed24d8d3815129394d7ea9c4603b4422184838` |
| `auditor.py` | `42515f709ab223e8c75f594b742dbde0e8e8d0adc20514b33fc1093c2182a778` |

Construction package file hashes:

| File | SHA-256 |
|---|---|
| `apply_oracle_boundary_patch.py` | `c9d0dd64b5a4dd51da6b2640381687eb53541355562f1a58be336aa0569b6c28` |
| `test_oracle_boundary.py` | `a2f2371fd366d3e7dc5f52e7bd5de433c9c9edafc8c2580c500d5c85c8cab91e` |
| `verify_construction.py` | `492d4390e9297b12e7c818c214007c98b86d53ff7398a57afea9d62077adaa8f` |
