# Authority binder byte-pin restart gap v1

Task: `O3-AUTHORITY-BINDER-BYTE-PIN-GAP-20260916-007`  
Issue: #204  
Immutable base: `505d567ff269ecec3ac8ff81e35fc7816a787a6d`

## H

The retained #203 wrapper fixes call ordering, but durable metadata pins only receipt-validator bytes. If identity-binder source changes between processes, the same authority epoch may be reinterpreted under different identity policy while the validator sidecar still reports a valid unchanged pin.

## T

A source-first, offline separate-process counterexample changed exactly one active source file between control and treatment: the identity binder. The diagnostic drift fixture preserves all retained terminal, expiry, verified-empty-release and release-token checks. It changes only caller-ID mismatch handling: a supplied nonempty caller ID is preserved instead of rejected.

Frozen source identities:

- exact bound issue wrapper: `2f812a678b72f09985e24d003b2e7030508a49e4475e9d3aef5533b1a07f2ba2`
- exact retained binder: `a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730`
- diagnostic drift binder: `e75b6851f37525e6230cde448392a248edf78d10c3e38dc2aeba4a518384ad26`
- byte-bound ledger v3: `a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5`
- bridge-v2 validator: `f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9`
- formal runner: `5704b29f11acc08519fbeca708898ac043dfce9432f3fbd7f9793dacb537a83d`
- process worker: `37a0e538a3956c9616d9e63f44b89d7a93868905df9af0bbf0bc45cc98b420da`

## First outcome

Result ID: `authority-binder-byte-pin-gap-v1-20260916-01`  
Formal retries: **0**  
Hard gates: **5/5 PASS**  
Decision: **`RETAIN_BINDER_VERSION_GAP`**

1. Process A with the exact retained binder issued only `runtime-intent-token` for post sequence 11.
2. A fresh control process with the same binder rejected `caller-forged-id` and left only the runtime-owned pending entry.
3. After replacing only the binder source with the diagnostic drift fixture, a fresh process accepted `caller-forged-id` for the same terminal and persisted a second pending entry alongside `runtime-intent-token`.
4. The validator sidecar stayed byte-for-byte semantically unchanged and continued to pin bridge-v2 SHA-256 `f16ba93...`; every non-binder source hash was unchanged.
5. Restoring the exact retained binder did not repair history: a new process could still recover the forged pending ID.

Formal-result SHA-256: `c4957cdf93d3939078f6b6928bcd2af54615e80f0e76256eb55637e458a7914b`. Independent audit: PASS with no errors.

## D

Retain the gap. Correct ordering is necessary but not sufficient for restart-stable identity semantics. The durable composition identity must cover the identity binder as well as the receipt validator before the wrapper can be treated as a restart-stable authority boundary.

The next narrow question is the representation of that pin. Two plausible mechanisms are:

- independently persist binder ID/SHA alongside the existing validator pin; or
- persist one composite composition-manifest identity covering binder + validator + function names.

The next experiment should compare these only on fail-closed restart behavior and crash-safe initialization, not on live GUI behavior.

## C

The drift fixture is an explicit diagnostic counterexample, not a proposed implementation and not evidence of a realistic accidental code change frequency. The claim is version/provenance binding across process restart, not hostile in-process isolation.

## U

No live GUI/model/network/durable-submit claim. PR #168 executed-source provenance remains independently unresolved and still blocks the downstream live crash-after-send allocation.
