# Issue #3152 — local Docker/host IPC construction probe

## H / T / D / C / U

**H.** This PC can run the repository host-local Codex broker alongside Linux Docker and complete one bounded, non-authoritative model request over the shared-filesystem IPC bridge without Windows/WSL executable interop.

**T.** Construction probe only; no formal #3152 allocation. One single-request handle IPC message, no image, using the checked-out branch broker from experiment/gpu-photometric-2912-20260921 at db244702566edd89aa163614856ae5e8ec11ca0c. Model: gpt-5.6-luna, low effort; ephemeral, read-only, no task tools. The response schema required exactly {"probe":true}. Host executable version and digest are retained in RESULT.json; local profile MCP startup warning was observed and retained as a note.

Then ran the two existing broker/bridge contract suites from an immutable snapshot of the four source/test files in local Docker: python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9, linux/amd64, --network none, read-only root and mount, 1 CPU, 512 MiB, 64 PIDs, no-new-privileges, all capabilities dropped. No model was called by these tests.

**D.** The IPC broker returned code 0; retained JSONL has one thread.started, one item.completed containing the exact schema response, and one turn.completed with 10,199 input / 15 output tokens. Broker elapsed interval was about 8.13 s. Docker tests: 18/18 passed, including symlink/path escape rejection, asset-hash refusal, authority refusal, timeout accounting and fail-closed bridge contracts. The transcript is retained and SHA-256 pinned in RESULT.json; audit.py reparses it and reconciles message/usage fields.

**C.** An initial request with mismatched shared-volume path placement was refused before host CLI invocation (model calls 0). A subsequent request passed path, schema and instruction hashes and reached the host CLI. Windows-native tests first passed 17/18; the remaining test could not create a symlink due to Windows privilege and was not an implementation failure. The first Docker snapshot run had 14 import errors because the expected runtime.* package layout was missing; after correcting the snapshot layout (not changing source), the pinned run passed 18/18. All attempts are disclosed; no failed allocation was retried because these were construction/test-harness checks, not a formal allocation.

**U.** This proves one local host-CLI IPC construction path and one bounded suite run for the exact checked-out branch snapshot. It does not establish current-main broker safety, equivalence to the separate app-server client, typed-vs-scalar evidence admission, any held-out recovery case, GUI/task effect, or #3152 acceptance. Inference used the configured Codex model endpoint; this experiment did not use a local GPU or train a model. Formal allocation count remains 0; keep #3152 open.

## Source provenance and integration boundary

The broker blob was 8aa0cd7058f0c494ccc691beeaa6827c363c89b3 in the tested branch; its SHA-256 and the other three tested file identities are in RESULT.json. The snapshot is branch-specific and is not claimed to be the version on GitHub main. In particular, do not infer that these stronger path/digest checks are already present on main. The test evidence supports a small, isolated candidate for a main-based integration PR after independent review.

The Docker result is local construction evidence. GitHub Actions is not the experiment runner.
