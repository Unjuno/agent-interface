# Issue #4924 — one Chromium fixture task-effect allocation

## H — Hypothesis

After the actual historical `session_v4.py` CLI emits `ready`, one bounded
Chromium program can navigate to its session-owned private fixture, enter the
exact per-seed token supplied by that event, submit the fixture form, and
produce output that the independent evaluator scores as an exact match.

## T — Test

- Preregistered on Issue #4924 before execution. Allocation
  `issue2922-chromium-task-effect-20260928-r1`, seed `992928`, one formal
  session, no retries. The nine ordered steps and decision gates are frozen in
  the Issue. A drafting arithmetic error there (6/8 steps vs the nine listed)
  was corrected in the Issue before formal execution; no allocation had yet
  started.
- Historical source base `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`; all eight
  source hashes were checked before startup and retained in the raw receipt.
- Runner SHA-256:
  `ad207a27231259f99961dc5875a28097887aca48e02d3c9adff769f0dabf72d4`;
  pre-formal runner/auditor/test commit `594f1800e9525fd794a3e6d44e20ee60f5e0a9e2`.
- Parallel-work collision: another worker independently froze an alternate
  nine-step probe in commit `910912761d608561f499561221751ef7dcb2b168`, SHA-256
  `7a67c411c32a626524f0575e9cef2ba6988130ad55886bc1ebb6019485db7b75`.
  It is retained and checksummed as an unexecuted alternate; only the runner
  hash above drove this allocation. No duplicate allocation was run.
- OrbStack Docker 29.4.0; image
  `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`
  (`linux/arm64`, CPython 3.11.2). No network, read-only source and runner,
  1 CPU, 1536 MiB, pids 256, bounded tmpfs, no-new-privileges, all capabilities
  dropped; only fresh `/out` writable.
- Exact one-time container invocation (formal output was
  `/tmp/unjuno-4924-task-effect-r1.XwihqG`):

```sh
/Users/taka/.orbstack/bin/docker run --rm --pull=never --network none \
  --read-only --cpus=1 --memory=1536m --pids-limit=256 \
  --security-opt=no-new-privileges --cap-drop=ALL \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=256m \
  --mount type=bind,src=/tmp/unjuno-2922-pinned-01349,dst=/repo,readonly \
  --mount type=bind,src=/tmp/unjuno-2922-chromium-nav-main-20260928/research/integration/golden_ipc_source_closure_2922_v1/private_endpoint_task_effect_r1/run_task_effect.py,dst=/runner.py,readonly \
  --mount type=bind,src=/tmp/unjuno-4924-task-effect-r1.XwihqG,dst=/out \
  --workdir /repo --entrypoint python3 \
  sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  /runner.py
```

The ready event supplied token `t992928`. The sole bounded program navigated
to the private URL, waited for the ready page, typed that token, tabbed to Save,
submitted, waited for the saved title, and observed. No model or broker was
called.

## D — Data and disposition

**`PASS_CHROMIUM_FIXTURE_TASK_EFFECT_SCOPED`**; container exit 0. The executor
completed exactly 9 steps. Release verified with no keys held. Chromium showed
`AI FORM SAVED - Chromium`. The retained submitted bytes are exactly
`value=t992928` (SHA-256
`69530330230e494bc9c068910581bf1221fee633f2e4bf8eb9d19803aae1e953`), and the
independent evaluator returned `success=true`, actual `{"value":["t992928"]}`.
The raw trace records one executor program and 37 input-admission events. Eleven
PNG observations and eleven `.ait` artifacts are retained. Startup diagnostics
include `Xlib.xauth: warning, no xauthority details available`; it did not
prevent the task effect.

The separate raw auditor derives the token from the ready event, parses the
retained submitted bytes independently, checks the public saved title and
evaluator agreement, and verifies all eight historical source blobs and every
artifact hash. Result: `PASS_RAW_AUDIT errors=[]`. The host and pinned-image,
network-disabled OrbStack checks each passed 8/8 auditor tests (one positive,
seven mutation controls); all 33 manifest entries verified. The mutation suite
rejects altered disposition, release, evaluator, extra program, model call,
output bytes, and saved-page evidence.

## C — Constraints

One synthetic local Chromium form and one fixed image/source/seed. The token
was deliberately supplied by `ready`; this tests the post-ready GUI input and
effect path, not visual task understanding, model utility, broker/IPC, external
application behavior, reliability rate, performance, or product readiness.
The fixture has no server-side POST counter, so request count is not claimed.
An initial host artifact-copy command used the wrong path and stopped; the
formal run itself had completed, and the saved file was recovered from the
session output directory without rerunning the allocation.

## U — Unknown / next rung

This one exact-token fixture effect is established only for the pinned
allocation. The host-broker/IPC route, independently grounded visual target,
model-in-loop behavior, and broader task transfer remain untested.
