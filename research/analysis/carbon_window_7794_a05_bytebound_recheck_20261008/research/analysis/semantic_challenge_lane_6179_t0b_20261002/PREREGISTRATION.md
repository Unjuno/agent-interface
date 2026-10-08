# Issue #6461 / #6179 T0b — executable broker-boundary controls

Allocation: `6179-T0B-EXECUTED-BROKER-CONTROLS-20261002-01`.

## H / T / D / C / U

**H.** In a finite broker/parser/normalizer/verifier model, an in-path challenge detects each seeded responsive semantic fault before a dependent ordinary verdict is released, while executable outer-broker/reducer functions reject forged-tag, old-generation replay, and challenge-to-ordinary-lane attacks. Healthy and healthy-slow routes remain usable, and challenge results never satisfy ordinary obligations.

**T.** Six challenge vectors, in frozen order: valid PASS; stale generation; missing mandatory evidence; revoked authority; contradictory receipt; wrong source/target. Route conditions: healthy, healthy-slow, stuck-at-PASS, stale-generation cache, parser omission, and skipped mandatory predicate. Compare heartbeat-only, detached startup probe, and in-path challenge. The two baselines do not exercise the subject's current verifier path; they may release an ordinary verdict without detecting a responsive semantic fault. In-path mode runs all vectors and gates release on exact typed results. The outer broker records every submitted envelope and decision. Attack envelopes are executable inputs: forged capability/tag; replayed old-generation PASS; challenge-lane PASS presented as ordinary evidence. The reducer/publisher/actuator boundary functions must reject them and append no ordinary receipt/effect.

One construction suite, then one WSLc candidate invocation, then one distinct raw-only audit invocation, each at most once; candidate/audit proceed only after the prior exit is zero. No retries. Native WSLc, pinned cached linux/amd64 Python image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, network none, one CPU, 1 GiB, uid/gid 65534, read-only source/input binds, fresh output bind. No Docker/Podman, GPU, model, GUI, live verifier, user data, or external effects.

**D.** PASS_METHOD_SCOPED only if every seeded fault is detected by the in-path challenge before any dependent ordinary verdict; heartbeat-only and detached-startup baselines expose their expected misses; healthy and healthy-slow do not end in permanent failure; forged, replay, and cross-lane envelopes are actually submitted and rejected; challenge-only inputs yield zero ordinary reducer, publisher, obligation-satisfaction, and actuator effects; an independent raw-only audit reconstructs all rows with zero errors. Any accepted attack, missed in-path fault, false healthy failure, leakage, or audit discrepancy is FAIL_METHOD. A failed start/resource gate is STOP before candidate, not a scientific verdict.

**C.** Deterministic authored state machine, parser, challenge vectors and timing. Capability is a symbolic fixture secret, not cryptography. Candidate and auditor implementations are separate but share this preregistration.

**U.** Synthetic protocol method test only. It establishes no cryptographic unforgeability, real process/tenant isolation, production-code-path equivalence, real verifier reliability, unknown-fault coverage, GUI safety, or field failure rate. The preceding #6179 T0 HOLD remains unchanged.
