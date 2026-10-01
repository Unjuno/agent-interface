# Issue #6074 T0 — interval robustness finite-method probe

## H / T / D / C / U (frozen before execution)

- **H:** On a finite GUI-like numeric trace corpus, interval robustness separates stable threshold truth/falsity from threshold-fragile nominal labels, and refuses claims when coverage or identity is unsupported.
- **T:** Evaluate the frozen cases in `cases.json`: clear spatial interior, threshold-straddling spatial value, clear exterior, near-deadline latency, exact zero-margin boundary, a possible between-sample short threshold crossing without a rate bound, uncertain timestamp ordering, missing sample/coverage, and discrete focus/coordinate/clock identity mismatch. Compare nominal point labels to interval dispositions. Verify each supported numeric result against an independently implemented endpoint oracle and mutations that widen bounds or remove provenance.
- **D:** `METHOD_PASS_SCOPED` only if robust TRUE/FALSE cases are invariant over all declared endpoint perturbations; boundary, incomplete-coverage, uncertain-order, or provenance-mismatch cases are UNKNOWN; independent oracle and mutation checks pass. Any false robust claim is FAIL; no discriminating cases is HOLD.
- **C:** Conservative threshold or fresh observation may be simpler; broad bounds can make the method uninformative; numeric uncertainty cannot resolve semantic identity.
- **U:** This is finite observed-trace method evidence only. It does not calibrate GUI error bounds, cover unobserved time, certify semantic effects, authorize actions, establish runtime integration, or show task benefit.

No model, GUI, input, external allocation, or formal live task is used. Candidate and oracle are separate implementations. No retries.
