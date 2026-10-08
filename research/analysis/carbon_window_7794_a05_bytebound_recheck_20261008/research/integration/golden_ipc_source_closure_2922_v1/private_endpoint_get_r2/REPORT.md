# Issue #2922 — actual CLI ready event and private endpoint GET

## H — Hypothesis

With the historical eight-file source closure hash-pinned, the actual
`session_v4.py` CLI can start its private Chromium/Xvfb session, emit `ready`,
and expose that session's loopback fixture endpoint to a GET from inside the
same isolated container before any task allocation or input.

## T — Test

- Allocation: `issue2922-session-cli-endpoint-get-20260927-r1`; seed `992926`.
- Repository source base: `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`.
- The probe verified all eight source SHA-256 values before launching the CLI;
  `session_v4.py` also emitted its own `sources.json`. Probe SHA-256:
  `9e8f8d8751fd799dd25b9c97ca78a111a6f61f9ab2b4068de09fe38995e47fc1`.
- Runtime image ID:
  `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`
  (`linux/arm64`, CPython 3.11.2); OrbStack Docker server 29.4.0.
- Source mount was read-only, network was disabled, and only `/out` was
  writable. Exact invocation:

```sh
/Users/taka/.orbstack/bin/docker run --rm --pull=never --network none \
  --read-only --cpus=2 --memory=2g --pids-limit=256 \
  --security-opt=no-new-privileges --cap-drop=ALL \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=256m \
  --mount type=bind,src=/tmp/unjuno-2922-pinned-01349,dst=/repo,readonly \
  --mount type=bind,src=/tmp/unjuno-2922-cli-r2.seC7QV,dst=/out \
  --workdir /repo --entrypoint python3 \
  sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  research/integration/golden_ipc_source_closure_2922_v1/session_cli_endpoint_get_probe.py
```

The driver waited for the actual CLI's JSON `ready` event, then issued one GET
to that event's exact `127.0.0.1` URL and sent `finish` only. It did not send a
`submit`, UI input, task action, or model request. Raw CLI events, source
receipts, exact initial observation (`about:blank`), PNG, and `.ait` are under
`raw/session/`.

## D — Data and disposition

**`PASS_CLI_READY_PRIVATE_ENDPOINT_GET_NO_TASK`**, container exit 0. The CLI
emitted `ready`, then one exact initial observation. The same-container GET
returned HTTP 200, `text/html; charset=utf-8`, 187 bytes, containing
`AI FORM READY`. The terminal `finish` caused the independent evaluator to
report `success=false` and `FileNotFoundError` for submitted output. There
were zero submit commands, zero input-admission events, and zero model calls.
The container execution took 5,197.718 ms.

The probe's `probe_POST_calls_issued=0` is a count of calls made by this
driver. The server did not expose a POST counter, so a total server-side POST
count is **not instrumented**. No GUI navigation occurred: Chromium remained
at `about:blank`; the HTTP client performed the GET.

The retained setup diagnostic includes the Xlib xauth warning; the initial
screen also shows Chromium's expected `--no-sandbox` warning from the fixture
runner. Neither prevented startup, observation, or the loopback GET. The
response body itself was consumed in memory and was not retained verbatim.

Independent raw auditor: `PASS_RAW_AUDIT`, `errors=[]`. Eight local tests
cover the baseline and rejection of mutated result/source/event claims.
The HTML response bytes were consumed in memory and not retained verbatim;
the recorded HTTP metadata, byte count, and marker check are the retained
response evidence.

## C — Constraints

This validates the actual CLI's pre-task `ready` event and same-container
session-owned endpoint reachability for one synthetic allocation. It is not a
Chromium navigation, a broker/IPC exchange, an allocated task, task-effect
success, or product acceptance. Earlier startup HOLD/STOP evidence and the
separate host-only GET result remain unchanged.

## U — Uncertainty and next rung

The Issue's pre-task CLI-ready plus private-endpoint GET boundary now has a
fresh container result. The next distinct integration rung is Chromium
navigation to the same session URL (without submitting the form), with
independent request and zero-output instrumentation. Keep task effects and
model authority out of that rung. An integration worker should independently
revalidate this retained allocation from main before promoting the result.
