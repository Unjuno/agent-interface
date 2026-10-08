# Issue #2922 — Chromium navigates to its session-owned endpoint

## H — Hypothesis

After the actual `session_v4.py` CLI emits `ready`, one fresh, explicitly
bounded navigation program can make Chromium request that session's private
loopback URL and render the fixture page without submitting the form or
creating task output.

## T — Test

- Allocation: `issue2922-session-cli-chromium-navigation-20260928-r1`; seed
  `992927`. This is distinct from the HTTP-driver GET allocations in R1/R2.
- Source base: `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`; all eight historical
  source hashes checked before CLI start and emitted again in `sources.json`.
- Runner SHA-256:
  `11758084745384736c2c4b067483c8052f4eca79c106ccbacce30adf086e5b6f`.
- Runtime: OrbStack Docker server 29.4.0; image
  `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`
  (`linux/arm64`, CPython 3.11.2). Source mount read-only, network disabled,
  1 CPU, 1536 MiB memory, bounded `/tmp` and `/dev/shm`; only `/out` writable.
- Exact invocation:

```sh
/Users/taka/.orbstack/bin/docker run --rm --pull=never --network none \
  --read-only --cpus=1 --memory=1536m --pids-limit=256 \
  --security-opt=no-new-privileges --cap-drop=ALL \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=256m \
  --mount type=bind,src=/tmp/unjuno-2922-pinned-01349,dst=/repo,readonly \
  --mount type=bind,src=/tmp/unjuno-2922-nav-r1.XWFza5,dst=/out \
  --workdir /repo --entrypoint python3 \
  sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  research/integration/golden_ipc_source_closure_2922_v1/session_cli_chromium_navigation_probe.py
```

The driver waited for `ready` and initial observation sequence 1, then submitted
one 5-step, 15-second-validity-bounded program: focus the browser address bar,
type only the session URL, press Return, wait for public title `AI FORM READY`,
and observe. It sent no form-submit program; after verified key release it sent
`finish` only.

## D — Data and disposition

**`PASS_CHROMIUM_PRIVATE_ROUTE_NAVIGATION_NO_TASK`**, container exit 0. The
executor completed all five steps with verified release and `keys_down=[]`.
Two observations showed `AI FORM READY - Chromium`; the retained final PNG
visibly shows the fixture page and its empty form. The independent evaluator
reported `success=false` and `FileNotFoundError` for submitted output. There
were 28 bounded input-admission events for address-bar navigation, zero
model calls, and zero form-submit steps.

Raw `events.jsonl`, all seven exact observation PNGs and `.ait` files,
`sources.json`, setup diagnostics, driver stdout/result, and `SHA256SUMS` are
retained under `raw/`. Independent audit: `PASS_RAW_AUDIT errors=[]`; eight
auditor tests (one positive and seven mutation controls) pass.

## C — Constraints

This proves that Chromium itself navigated to the session-owned loopback page
inside this one no-network container. It does not prove a broker/IPC path,
task allocation, form submission, task-effect success, or product acceptance.
The probe did not instrument the fixture server's POST counter; its own plan
contains no form-submit step and the independent evaluator found no output.
The response body was not retained verbatim. An unrelated OpenFOAM container
used about one CPU concurrently; this is not a latency/performance comparison.
The Xlib xauth and Chromium `--no-sandbox` notices are retained in diagnostics/
the screenshot and did not prevent this run.

## U — Uncertainty and next rung

The CLI-ready → bounded Chromium navigation → rendered private page boundary
is now exercised with a separate fresh seed. Task-effect semantics remain
unverified and must not be inferred from this navigation pass. An integration
worker should independently replay this result from main; any form-submit or
application-effect experiment is a separate allocation with its own frozen
oracle and explicit scope.
