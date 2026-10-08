# Issue #8470 T0 A01 — compositional gain-margin finite method test

**Disposition: `PASS_METHOD_SCOPED`.** The one frozen candidate run and the one independent exact-rational audit completed with exit 0. The auditor reconstructed all eight rows, found zero mismatches, rejected all three preregistered gain-matrix mutations, and passed all nine decision gates. This is a finite synthetic method result only.

## H / T / D / C / U

- **H:** Individually passing components do not ensure a safe composition. A conservative gain envelope including cross-axis coupling, delay, hold duration, actuator response, and release residual should refuse composed failure while retaining positive controls.
- **T:** Eight frozen exact-rational two-feature cases; current/delayed feature terms, estimator error, disturbance, saturation, requested/max hold, fixed delay-jitter schedule, actuator/controller coupling, and one-step release residual. Candidate once, independent auditor once. Freeze and commands are in [`FREEZE.json`](FREEZE.json) and [`PREREGISTRATION.md`](PREREGISTRATION.md).
- **D:** Passed: positive C01/C03 certified; C02 component checks each pass but coupled envelope is unstable and trajectory crosses the feature bound; C04 unit boundary remains bounded-nonconvergent; C05 stable envelope is conservatively rejected; C06 release-tail path is included and refused; C07 invalid hold cap is refused; C08 estimator/disturbance-driven finite escape is refused; no crossing row is certified; three mutations rejected.
- **C:** Direct finite reachability may be simpler or stronger for the declared finite family. The sufficient screen rejects some stable systems; C05 demonstrates that conservatism. The fixture is authored and gain values are stipulated, not estimated from a real interface.
- **U:** No inference to real subsystem-gain identification, arbitrary switching/jitter, real input timing, GUI semantics, irreversible effects, model behavior, game success, safety, or product performance. C03's scheduled delays and C06's one-step release residual are finite abstractions, not empirical runtime timing.

## Formal results

| Case | Exact observed result |
|---|---|
| C01 uncoupled positive | `CERTIFIED`; maximum row gain 2/5; peak feature 1 |
| C02 cross-coupled unstable | every isolated component check passes; `UNSTABLE_ENVELOPE`; refused; crosses bound 2 at step 4, final peak 390625/65536 at step 8 |
| C03 delayed/jittered, shared actuator | maximum scheduled delay 2; `CERTIFIED`; maximum row gain 123/200; peak 1/2 |
| C04 unit boundary | `BOUNDED_NONCONVERGENT_ENVELOPE`; refused; no finite-bound crossing |
| C05 conservative reject | `STABLE_ENVELOPE`, maximum row gain 1; refused without an instability label; peak 1 |
| C06 release lag | release contribution present; maximum row gain 1; refused; finite peak 12442849/781250, above 2 |
| C07 held-input cap | requested hold 3 exceeds cap 2; contract invalid; refused |
| C08 estimator + disturbance | maximum row gain 4/5 but finite peak 45172/15625 exceeds 2; refused |

The C02 unsafe composition is detected before any certification; C06 and C08 show why the separate release and finite-feature gates matter even where a simple matrix status alone is insufficient. This finite suite does not establish soundness outside the authored family.

## Execution and evidence

Base main at freeze: `8d2eac460a7744d049bbca1d25b3cde86b1b496c`. The exact case file, candidate, independent auditor, preregistration, construction test hashes, and one-shot budget are bound by [`FREEZE.json`](FREEZE.json). Candidate raw is [`CANDIDATE.stdout.json`](CANDIDATE.stdout.json); independent audit is [`AUDIT.stdout.json`](AUDIT.stdout.json); exits and empty stderr are retained. Full file checksums are in [`SHA256SUMS.txt`](SHA256SUMS.txt).

Python 3.12.10, standard library, exact `Fraction` arithmetic, CPU-only in the attached local execution environment. No Docker/WSLc command, game, GUI, model, GPU, external service, or live input was used. The WSLc ownership gate was not touched; no running container or experiment was inspected or stopped. This allocation neither required nor measured container isolation/performance.

The candidate and auditor formal invocations each ran exactly once. No retry or post-result source change occurred. This result does not repair, replace, or retry historical #6195 allocations, and does not close parent #59 or claim real-control evidence.
