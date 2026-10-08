# Issue #6483 T0 formal result

This directory contains the one preregistered method-only candidate invocation and its one independent audit. The source package and decision rules remain frozen in the sibling `effect_critical_principal_binding_6483_t0_20261002/` directory; do not edit those inputs to reinterpret this result.

## Outcome

`METHOD_PASS_SCOPED` on a finite synthetic trace fixture only. Candidate and auditor each ran exactly once, both exited 0, and no retry occurred. The fixture assigned 9 scenarios × 4 policies = 36 rows.

- Wrong-principal actionable proposals: transcript-order 2; cluster-only 3; authenticated push-to-talk 1; segment/principal gate 0.
- Cluster-only produced 6 unauthenticated actionable proposals.
- Segment/principal gate preserved 3 clean controls and the explicitly authorized joint request; it yielded the ungranted joint request and mixed-principal context, and held stale/unauthenticated sources.
- Independent corruption controls all rejected: owner swap, cross-speaker negation splice, stale-generation refresh, cluster confidence treated as identity, and assigned-denominator mutation.
- Quoted commands remained non-actionable.

These are deterministic synthetic-method results. They do not establish live source identity, liveness, consent, diarization robustness, production voice behavior, or action safety. No audio, model, human participant, GUI action, or external effect was used.

## Runtime and resource caveat

Microsoft WSL Containers CLI `wslc.exe` 5.0.1.1, which reported WSLc runtime 3.0.1.0, ran pinned `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (Python 3.12.14, linux/amd64), network disabled, 1 CPU requested, 512M requested, GPU disabled. Both invocations emitted the WSLc warning that swap-limit/cgroup capabilities are unavailable. Memory enforcement is therefore unknown; no enforced memory limit is claimed.

## Preserved evidence

- `candidate/`: raw candidate JSON, status, exact stdout/stderr bytes, and host-recorded WSLc exit code.
- `auditor/`: raw audit JSON, status, exact stdout/stderr bytes, and host-recorded WSLc exit code.
- Candidate JSON SHA-256: `c69efc42b36731b2e3f9707d9224dc629ec7c03992379260a48cbeae73938f31`.
- Audit JSON SHA-256: `a6abfb6930d0da67d57de5265180b4316968a9510da80bf3b55cc05f2a02f6fc`.
- Both stdout/stderr streams and complete invocation metadata are retained in their respective status JSON and `.bin` files.

The preregistered base main was `b77e894138afaacbc6eb43cb08bc12873e276f67`; the registered experiment branch commit was `9eb37dabe921664ad35751fcf76eefa395849c0c`. Formal runs followed the post-registration gate with main still equal to that base, the exact branch unchanged, all 12 frozen package hashes verified, and no running WSLc containers.
