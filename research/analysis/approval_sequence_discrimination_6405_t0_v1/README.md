# Issue #6405 T0 — approval-sequence discrimination method fixture

Status: prepared, formal T0 not yet run. Allocation is a no-participant, no-effect synthetic protocol check. No human response, attention, approval wisdom, security efficacy, or product claim is inferred.

## H / T / D / C / U

**H.** Holding the request sequence and broker digest rule fixed, the finite protocol can present all source fields in each arm, highlight only source-bound changed effect fields in B, and batch only eligible nonconsequential repeated requests in C without reusing an old receipt or losing individual scope/expiry/deny/cancel boundaries.

**T.** Nine frozen scripted requests across three arms (27 rows): five benign repeated single-note requests; one rare changed-recipient consequential request; one valid new read-only request; one explicit denial; and one late scope expansion superseding R01. Arms: A identical static layout; B exact source-bound changed-field salience; C consecutive nonconsequential repeated requests grouped while retaining each row's independent request digest, expiry, approval/deny controls, and receipt. One candidate emits the fixture and a separate raw-only auditor reconstructs it. No participants, GUI, model, broker, network, task effect, actual money, credentials, or user data.

**D.** `METHOD_PASS_SCOPED` only if every row displays the exact principal/recipient/target/effect/scope/expiry; B highlights exactly the changed fields; C batches only the five eligible repeated requests without batch-level authority; deny/cancel remain visible; every approved receipt binds one request digest/principal/scope/expiry; denial mints no receipt; late scope change gets a new digest and receipt. Independent auditor must reject omitted field, swapped recipient, stale highlight, overbroad batch, and prior-receipt reuse. Any mismatch is `FAIL_METHOD`; no human-behavior claim follows a pass.

**C.** Exact digest binding may make visual salience unnecessary; a clear one-line change summary may dominate; repeated requests are scripted and cannot reproduce fatigue or attention; the batching arm may be ineligible in real policy.

**U.** T0 verifies fixture/protocol/auditor integrity only. It says nothing about actual human detection, false-approve rates, attention, fatigue, usability, consent, live broker integration, or safer choices. T1 requires separate voluntary consent, privacy/accessibility review, and preregistration.

## Frozen execution policy

Branch `research/approval-sequence-discrimination-6405-t0-20261002`; additive path is this directory. Base and image/source/script/input identities are in `FREEZE.json`. Construction suite runs before the one-shot container candidate. Candidate cap 1; independent raw-only auditor cap 1 only on candidate exit 0; retries 0. Pinned cached Linux/amd64 image, no pull, network disabled, read-only code/input and separate output mount. Outputs are retained as `results/t0-01/raw.json` and `audit.json`. The image/runtime is an execution boundary only; no memory-isolation claim is made.

The host offers OrbStack but not WSLc. This T0 is executed in OrbStack solely as a user-requested isolated CPU container; no cross-runtime portability conclusion is made. Do not use any result to claim human behavior or live authorization validity.
