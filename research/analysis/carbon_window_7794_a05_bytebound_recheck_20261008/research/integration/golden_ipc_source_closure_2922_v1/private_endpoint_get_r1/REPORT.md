# Issue #2922 — private endpoint GET first-rung

## H — Hypothesis

With the historical eight-file source closure hash-pinned, the GUI session setup
used by `session_v4` can start its Chromium fixture server inside the isolated
runtime container, and a GET from that same container to the session-owned
loopback endpoint returns the fixture page without creating submitted output.

## T — Test

- Allocation: `issue2922-private-endpoint-get-20260927-r1`; seed `992925`.
- Repository source base: `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`.
- The eight source files were SHA-256 checked against the already merged
  `SOURCE_MANIFEST.json` before session startup. The exact experimental runner
  is `../endpoint_get_probe.py`, SHA-256
  `5768fefdba069770ba20ac0354aee295b5f2b4ba5e571c6813c1390d52a336c2`.
- Runtime image: `issue-2849-task1-runtime:v3-20260921`, immutable image ID
  `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`,
  Linux/arm64. OrbStack Docker server 29.4.0, host client reports linux/aarch64.
- Exact command:

```sh
/Users/taka/.orbstack/bin/docker run --rm --pull=never --network none \
  --read-only --cpus=2 --memory=2g --pids-limit=256 \
  --security-opt=no-new-privileges --cap-drop=ALL \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=256m \
  --mount type=bind,src=/tmp/unjuno-2922-pinned-01349,dst=/repo,readonly \
  --workdir /repo --entrypoint python3 \
  sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  research/integration/golden_ipc_source_closure_2922_v1/endpoint_get_probe.py
```

The runner started a private Xvfb-backed `gui_suite.Session`, called the same
`gui_suite.prepare(..., "chromium", ...)` path used by the runtime, then issued
one HTTP GET to the exact loopback URL returned by that session. Network mode
was `none`; no provider/model, task, UI input, or POST was invoked by the probe.
The runner cleans up only its own server, X session, and temporary directory.

## D — Data and disposition

**`PASS_PRIVATE_ENDPOINT_GET_NO_OUTPUT_MUTATION`**, container exit 0. Session
startup completed in 1,459.521 ms. GET returned HTTP 200, `text/html; charset=utf-8`,
187 bytes, containing `AI FORM READY`. The session's submitted-output path was
absent both before and after the GET. The raw stdout and normalized result are
retained as `RAW_STDOUT.txt` and `RESULT.json`.

The runner's raw `post_requests: 0` field is initialized by the harness; it is
not a server-side request counter. The defensible statement is that this probe
issued no POST call. Total server POST count was **not instrumented**.

## C — Constraints

This is one private synthetic fixture, same-container loopback GET, and
session-preparation component result. It is not the `session_v4.py` CLI's
`ready` event, Chromium navigation to the endpoint, a broker/IPC exchange,
task allocation, task effect, or product/runtime acceptance. The Xlib xauth
warning was emitted, but setup and endpoint request completed normally. No
historical source or predecessor result was modified.

## U — Uncertainty and next rung

The endpoint's existence and GET response are now verified from the same
session/container. Still unverified: that the actual `session_v4.py` process
publishes the expected ready event before allocation and that Chromium itself
navigates to and observes this URL in the integrated route. A distinct next
rung should invoke the actual CLI once with a fresh seed, observe its ready
event, make the endpoint GET, send `finish` only, and independently audit the
event stream and no-output boundary. Do not infer task-effect success.
