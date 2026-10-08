# Issue #5970 T2b — corrected prospective trace attempt after preflight STOP

## Why this is a distinct successor attempt

The original T2 candidate was invoked once and stopped before creating a run directory: it compared the frozen count of 324 regular archive files with 425 total tar entries (324 files + 101 directories). No Xvfb, Tk, observer, or XTest input was started. Preserve that STOP as `candidate.preflight_stop.raw.json`; do not edit or rerun `candidate.py`.

T2b is a new, versioned candidate and a separate output directory. It corrects only the inventory predicate to count regular files, independently verifies the original STOP, and then runs the already frozen two-event protocol once. This is not a retry of the consumed Issue #4135 formal allocation; no #4135 allocation is re-used.

## H / T / D / C / U

- **H:** The previously preregistered prospective provenance protocol can be executed on an isolated X11/Tk fixture after a fail-closed preflight validates regular-file inventory correctly.
- **T2b:** Reconstruct the same frozen #4135 archive, verify 425 total tar entries and exactly 324 regular files, independently adjudicate the T2 preflight STOP, then use the frozen T2 instrumented app/observer and runner on a fresh Xvfb display. Arm both streams before each Shift press/release, record two per-source acknowledgements and four tagged observations, and verify neutral terminal keymap. The Docker Desktop Linux engine remained unavailable; use the already-installed WSL2 Ubuntu 24.04 Xvfb stack, isolated from the user's desktop.
- **D:** Pass only if archive integrity/inventory is correct, each event has one matching app and observer record and explicit common actuation parent, all source-local event IDs/sequences are distinct/ordered, and the final Shift state is neutral. Preserve both the first-attempt STOP and T2b result; no retroactive rewrite.
- **C:** The positive result validates this serialized, test-only trace instrumentation path. It does not validate concurrency, arbitrary in-flight channel accounting, production integration, or logger overhead.
- **U:** Production-grade cross-process provenance, behavior under unsolicited/concurrent input, and benefit to real recovery decisions remain untested.

Candidate-v2 and the T2b independent auditor each run once. If either stops, retain it and do not repeat the live fixture run.
