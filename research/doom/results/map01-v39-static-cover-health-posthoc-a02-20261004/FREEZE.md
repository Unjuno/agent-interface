# V39 static-cover health response — posthoc A02

Status: preregistered raw-log analysis; no new live allocation. A01 is retained as STOP because its runner was not POSIX-parsable.

## H — Hypothesis
During accepted program `cover-5`, the runtime continues the already-accepted fixed four-cycle action sequence after a lower typed-health sample, with no recorded cancel/revocation before the external cancel request. The raw record can bound this stale-policy exposure window but cannot show that an alternative policy would improve task outcome.

## T — Test
Run the standard-library candidate parser and independent auditor against only the retained raw event stream from `map01-v39-coast-liveness-live-01`. Bind source manifest SHA-256 `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`; bind raw events SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`. Scope to `cover-5` and its immediately preceding typed sample from `plan-4-primary-0-1`. Check the accepted static step contract against execution records, calculate typed health/time bounds, order cancel/release/terminal events, and require the mutation negative control to be rejected.

## D — Decision
PASS if the 16-step static command is accepted and recorded through a later lower-health sample without a recorded cancel/revocation before the eventual cancel request, verified-empty release, and terminal record; the independent audit passes; and the altered health value is rejected. FAIL if raw evidence contradicts this. STOP if container/runner setup prevents test completion. A missing required record is UNCERTAIN.

## C — Competing explanations
The health change may reflect damage unrelated to a threat the chosen policy could address; sampling can miss intermediate state; the repeated policy could remain appropriate despite health loss; cancellation may be driven by a runner decision not recorded here. Missing guard-evaluation events cannot prove that no guard ran.

## U — Limits
Posthoc descriptive analysis of one completed live trace only; not a fresh allocation, matched comparison, causal survival estimate, threat adjudication, independent useful-feedback measure, recovery bound, or evidence a different policy would help. The trace ended with 1 kill, 0 deaths, no MAP01 exit. No additional Doom/VizDoom/X11 process will be started. Swap enforcement is not assumed.

## Frozen provenance
- Current-main base: `8094af4631fc7bc5d92990e5151d5e89477ee39f`.
- Raw events SHA-256: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- Source manifest SHA-256: `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`.
- Candidate SHA-256: `e6a51cc65e4f290470df8c8f5dc2fa127ec5c80223b9a504fc12af96e7d2f5a6`.
- Auditor SHA-256: `4bd4fe5047bff4da15475d682a77110eff0c07fb8f3545d90025972717383ad9`.
- LF-only runner SHA-256: `8dec0e0f7ac142edd3479ad119f2072e1b553b3c90dc1855e2cc57a8dc0a4770`.
- Cached runtime image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Command: `wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --mount type=bind,source=C:/w/keyupr3,target=/src,readonly python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f sh /src/research/doom/results/map01-v39-static-cover-health-posthoc-a02-20261004/run_a02.sh`.
