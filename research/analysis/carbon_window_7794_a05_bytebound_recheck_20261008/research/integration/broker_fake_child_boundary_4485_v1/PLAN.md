# Broker fake-child boundary experiment

Allocation: `broker-fake-child-boundary-4485-20260928-01`
Branch: `research/broker-fake-child-boundary-4485-20260928`
Additive result path: `research/integration/broker_fake_child_boundary_4485_v1/`
Frozen main at branch creation: `1b1b683a07b87edba6fb312600f09d28ea86b4ae`.
Broker source is main Git blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`;
the mocked regression-test reference is blob
`79405a089708a3f2d7c0982192592041125cf0dd`.

## H — hypothesis

The one-shot host broker will propagate a real fake-child exit 0 and exit 23
exactly, record timeout and unavailable-executable outcomes as typed
non-success without response text, avoid invoking the child for malformed
JSON, bound an idle `--once` process externally without emitting a receipt,
and process only the lexically first of two queued requests. Every path remains
non-authoritative.

## T — single local Docker allocation

Use the cached `python:3.12-slim-bookworm` image
`sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
on linux/amd64. Run one formal Docker invocation with network disabled,
`--pull=never`, read-only root and source, fresh output-only writable mount,
0.25 CPU, 256 MiB, 32 PIDs, dropped capabilities, no-new-privileges, and
bounded writable tmpfs for the disposable fake executable and broker tempdir.
The container will run seven cases: child exits 0; child exits 23; child
times out; executable missing; malformed JSON request; idle `--once` bounded
by the harness; and two queued requests with only the sorted first handled.
The fake child is generated in the container and only logs its argv/stdin and
returns deterministic text/status. It does not contact models, providers, host
tools, or the network. A separate raw-only standard-library auditor process
checks all seven outcomes and eight copied-evidence corruption controls.

Construction checks are limited to Python syntax/unit tests and Docker/image,
source-identity, and fresh-output preflight. They do not invoke the broker.
Formal experiment runs once; no retries or post-result changes.

## D — decision

PASS requires all seven expected outcomes, exact propagation of child statuses
0/23, typed timeout/unavailable results with empty response, no child call for
malformed JSON, bounded idle with no IPC outputs, exactly one response/call for
the lexically first queued request, `authority_granted=false`, zero raw audit
errors, and all eight corruption controls rejected. Any contradictory audited
case is retained as FAIL. Source/image/output/setup failures before invocation
are STOP, not scientific evidence.

## C — controls and confounders

Current-main broker bytes and the cached image are fixed; only child exit,
child delay, request validity, and queue composition vary by declared case.
The fake child is local and deterministic. Existing mocked tests are references
only; their results are not pooled. Do not stop or modify pre-existing
containers. GPU is not requested or used.

## U — limits

One host, one amd64 image, and seven fake-child requests. This tests only the
local OS subprocess-to-broker boundary. It says nothing about OrbStack
equivalence, real Codex/provider behavior, model quality, runtime authority,
GUI/task correctness, latency, or product readiness.

