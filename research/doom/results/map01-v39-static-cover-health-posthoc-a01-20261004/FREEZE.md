# V39 static-cover health response — posthoc A01

Status: preregistered raw-log analysis; no new live allocation.

## H — Hypothesis
During accepted program `cover-5`, the runtime continues the already-accepted fixed four-cycle action sequence after it has sampled a typed health decrease, with no recorded local cancel/revocation before the external cancellation. The raw record can bound this stale-policy exposure window but cannot show that an alternative policy would improve task outcome.

## T — Test
Run a standard-library parser against only the retained raw event stream from `map01-v39-coast-liveness-live-01`. Independently audit the candidate output from the same raw bytes. Bind source manifest SHA-256 `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`; bind raw events SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`. Scope to `cover-5` and the immediately preceding typed sample from `plan-4-primary-0-1`. Check the accepted static step contract against step-start/complete/key-held records, calculate typed health extrema and time bounds, and order cancel/release/terminal events. No frames or external footage will be interpreted.

## D — Decision
PASS if the retained stream shows the static sequence executing across successive typed health samples after a lower health value is observed, with no cancel/revoke event for `cover-5` before the first cancel request, and a separately ordered eventual cancel/release/terminal record. Otherwise report FAIL for the specific hypothesis or UNCERTAIN when required event evidence is missing or inconsistent.

## C — Competing explanations
The health change may reflect damage unrelated to a threat the chosen policy could address; sampled typed values may miss intermediate state; the repeated movement/attack sequence could be locally appropriate despite health loss; cancellation may be driven by a runner decision not present in this raw stream. A log that lacks explicit guard-evaluation records cannot prove that no guard was evaluated.

## U — Limits
This is posthoc descriptive analysis of one completed live trace. It is not a fresh allocation, matched comparison, causal survival estimate, threat adjudication, independently useful feedback measure, recovery bound, or proof that a different policy would have helped. The raw run's terminal score remains 1 kill, 0 deaths, no MAP01 exit. No additional Doom/VizDoom/X11 process will be started.

## Frozen provenance
- Current-main base: `8094af4631fc7bc5d92990e5151d5e89477ee39f`.
- Raw events SHA-256: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- Run source manifest SHA-256: `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`.
- Runtime image: cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Container plan: WSLc, source mounted read-only, `--pull never --network none`, 1 CPU, 512 MiB. Output is captured on the host. Resource enforcement is not inferred from flags.
- Frozen analysis target: command and observation events for `cover-5`; no live inputs or calls.

- Candidate parser SHA-256: `e6a51cc65e4f290470df8c8f5dc2fa127ec5c80223b9a504fc12af96e7d2f5a6`.
- Independent auditor SHA-256: `4bd4fe5047bff4da15475d682a77110eff0c07fb8f3545d90025972717383ad9`.
- Negative control frozen before container execution: replace candidate `cover_samples.last.health` with `999`; the independent auditor must reject the altered result.
- Command: `wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --mount type=bind,source=C:/w/keyupr3,target=/src,readonly python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f sh -c "python3 -B /src/research/doom/results/map01-v39-static-cover-health-posthoc-a01-20261004/candidate.py /src/research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl > /tmp/candidate.json && cat /tmp/candidate.json && python3 -B /src/research/doom/results/map01-v39-static-cover-health-posthoc-a01-20261004/auditor.py /src/research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl /tmp/candidate.json && python3 -B -c '"'"'import json; p=json.load(open("/tmp/candidate.json")); p["cover_samples"]["last"]["health"]=999; json.dump(p,open("/tmp/mutated.json","w"))'"'"' && if python3 -B /src/research/doom/results/map01-v39-static-cover-health-posthoc-a01-20261004/auditor.py /src/research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl /tmp/mutated.json; then exit 9; else echo NEGATIVE_CONTROL_REJECTED; fi"`.

- Frozen runner SHA-256: `19d534f87890354095fd6f0e310f800177509bd90f2415a6d1b35e055cdc6f76`.

## Provenance correction
The command line transcribed above as an equivalent inline sh -c invocation was not the literal invocation. The executed command mounted this checkout read-only and ran sh /src/research/doom/results/map01-v39-static-cover-health-posthoc-a01-20261004/run_a01.sh. The exact CRLF runner bytes (SHA-256 19d534f87890354095fd6f0e310f800177509bd90f2415a6d1b35e055cdc6f76) are preserved in un_a01_crlf.b64; decode that file to recover them. Its CRLF line endings explain the shell's expected-fi parse failure. A01 remains STOP.
