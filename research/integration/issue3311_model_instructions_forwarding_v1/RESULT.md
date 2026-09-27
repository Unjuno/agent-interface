# Issue #3311 — broker instructions-forwarding construction probe

## H/T/D/C/U

**H — hypothesis.** The current host IPC broker omits the request's `instructions` path from its `codex exec` command. Forwarding it through the CLI's `model_instructions_file` config should let the existing runner/broker boundary deliver its declared responder instructions without changing authority or transport behavior.

**T — bounded construction test.** Intake ref: main `77dce1b88eba67d3317290fe38cb4d35d92e3abb`; broker blob before change `f307daafdfd36d1ab4faf39bb36c36350e6e67e4`; test blob `e645ae575cd6fdae02556df9facc9919739584f3`. Run deterministic unit tests against `serve()`, replacing only `subprocess.run` with a mock. Cover /repo and /workspace path mapping, JSON quoting, and preservation of schema/image/prompt args. No Codex executable, provider/model call, GUI/input, network, or task allocation.

**D — observed result.** Local Docker Desktop Engine 29.8.0, linux/amd64, image `python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9`. Container used `--network none --cpus 1 --memory 128m --pids-limit 16 --read-only`, a 16 MiB tmpfs at /tmp, `no-new-privileges`, and dropped capabilities. Command:

```text
docker run --rm --network none --cpus 1 --memory 128m --pids-limit 16 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --security-opt no-new-privileges --cap-drop ALL -v <probe-dir>:/work:ro -w /work python:3.11-slim python -B -m unittest -v test_broker_model_instructions.py
```

Outcome: **4/4 PASS**, 0.004s. The local probe exercised a main-derived copy of the broker's `serve()` with the proposed config argument and mocked subprocess. Probe source SHA-256: broker copy `532E579EA91534190AF426193878D9E4AE6671B73CCB1A28441D37BBE1BC5C1A`; tests `8B6201B0EDDC986BFB75175F4920190E00EDA70BEC6DC37AFDC2ABC99A413A39`. This construction run predates/does not execute GitHub's committed test module byte-for-byte; CI must verify that exact production diff.

**C — controls and separation.** No retries or historical records modified. The patch adds only `-c model_instructions_file=<JSON-quoted host path>` built through existing `host_path()`. It does not change one-shot exit semantics (#4520), authority fields, request order, or IPC framing. PR #4637's incomplete synthetic roundtrip remains unpassed; this does not establish a live host CLI roundtrip or satisfy #3311.

**U — limits / next gate.** Await the exact PR checks/review. A green unit/CI result establishes only instruction-argument construction. A separate, frozen live endpoint preflight (Issue #3489 gate) is still needed before any #3311 allocation; do not retry prior formal allocations. No model, GUI, task-correctness, efficiency, latency, or product claim is made.
