# Issue #5036 — broker fake-child boundary successor

## H / T / D / C / U (frozen before execution)

**H — Hypothesis.** With only harness plumbing corrected, the current-main broker propagates fake-child exits 0 and 23; records timeout and unavailable as typed non-success with empty response; rejects malformed JSON without child invocation; externally bounds idle `--once` without IPC output; and for queued requests processes lexical-first `a` only. Every receipt keeps `authority_granted=false`.

**T — Test.** Allocation `broker-fake-child-boundary-4485-20260928-02`; seven isolated real fake-child process cases, one formal Docker invocation, plus construction-only syntax/unit/source/image/output gates and a disposable executable mount probe. Pin the broker Git blob, Docker image ID, source hashes, invocation, and output identity in `FREEZE.json`. Local Docker Desktop, linux/amd64; no GPU.

**D — Decision.** PASS requires exact child exit propagation (0/23), typed timeout/unavailable non-success with empty response, malformed JSON with zero child calls, externally bounded idle with no receipt, queued `a` only (one call/receipt/response; `z` untouched), all authority false, raw audit zero errors, and 8/8 corruption controls rejected. Any contrary fully executed case is FAIL. Source/image/mount/output/provenance gate errors are typed STOP, not a scientific conclusion; no retry.

**C — Competing explanations.** The #5013 STOP exposed harness defects (non-executable /tmp mount, absent `--once`, and BaseException catching normal SystemExit). Remaining mismatch may reflect broker semantics, case isolation, or audit/runner defects rather than the hypothesis.

**U — Uncertainty.** One Windows host, one cached amd64 image, seven synthetic cases. No OrbStack equivalence, real Codex/provider semantics, credentials/network/GUI/application effect, model behavior, latency, runtime authority, or product-readiness claim.

## Frozen scope

Preserve #5013 and PR #5034 unchanged. The only harness corrections are executable tmpfs permission, `--once` for every one-request case, and logging ordinary `Exception` rather than `BaseException`. Source broker must remain Git blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`. Image: `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; network none, pull never, root/source read-only, output fresh/writable, 0.25 CPU, 256 MiB, 32 PIDs, dropped caps, no-new-privileges, /tmp tmpfs rw,exec,nosuid,size=16m. Run only on local Docker Desktop; do not stop/modify pre-existing containers.