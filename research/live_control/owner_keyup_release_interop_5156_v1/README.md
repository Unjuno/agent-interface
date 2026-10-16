# Issue #5156 receipt protocol compatibility audit

## H / T / D / C / U

**H.** The merged #5175 synthetic release receipt contract accepts the autonomous release reasons and operation identities emitted by its pinned InputOwner v10 / transition-owner v3 sources.

**T.** Run the exact main-branch protocol module against all literal autonomous `release(reason)` branches parsed from the pinned owner source, plus one explicit integer `button_up` receipt in the identity shape emitted by the wrapper. Bind source Git blob IDs before test execution. Run once in pinned offline Docker; run an independent raw-result audit in a separate pinned offline Docker container.

**D.** `FAIL_RELEASE_RECEIPT_INTEROP` if any source-supported release form is rejected. `PASS_EXPECTED_COMPATIBILITY_FAILURES_REPRODUCED` from the independent auditor means the failure set was reproduced exactly; it does not mean the candidate contract passed.

**C.** Preserve all authority flags false. No InputOwner instance, X server, XTest/XSync, GUI, desktop input, model/provider, game, or network operation is permitted. The probe calls only the pure receipt validator.

**U.** Static/synthetic compatibility only. It does not establish a runtime timing result, physical key-up, safety rate, or MAP01 effect. The protocol file itself is byte-bound to current main; the owner and wrapper are Git-blob-bound to the Issue #5156 pinned dependencies.

## Provenance

- Frozen main intake: `53b93cd5dcb0fbbedee1db23ddf550ba1eb289e0`.
- `input_owner_v10.py`: `341b3c01649943ddaad5f28431a792c4889cc36e`.
- `input_transition_owner_v3.py`: `0ea631abcf6272f0538a9ef9198ad8069b47b464`.
- Merged #5175 `release_protocol_v2.py`: SHA-256 `3ae2ad7ca09bdd6572080aa55ce9fae9cb24a566629c95bf9736220098f134cd`.
- Docker image: `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` (linux/amd64, Python 3.12.14).

The additive research record is delivered under `research/live_control/owner_keyup_release_interop_5156_v1/`. A post-run default-branch check confirmed the three source Git blob IDs above remain unchanged at current main `317071858f3bc9e0d3d90330095b90c9835dc591`; see `CURRENT_MAIN_RECHECK.json`. This does not change the merged #5175 record or its historical result.
