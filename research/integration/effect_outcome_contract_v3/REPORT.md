# Effect outcome contract v3: pre-effect invariant-manifest binding

Task `EFFECT-OUTCOME-CONTRACT-V3-BINDING-20260916-001`, Issue #490.
Construction base: `f8d59b45afee0790c7713f5d5b7fab253d505de2`.

Decision: **`PASS_CONSTRUCTION_CANDIDATE_V3`**.

## Purpose

V2 made compensation completion depend on explicit required invariants and independently verified evidence. Its remaining boundary was temporal: the required-invariant set was still supplied at outcome-reduction time. A caller could therefore attempt to construct a narrower requirement set after observing the effect unless the executed command already carried the original contract identity.

V3 adds exactly that binding. `bind_invariant_manifest()` canonicalizes a non-empty scope plus unique named requirements and computes a SHA-256 manifest id. `ExecutionBinding` carries that id before the effect. `VerificationReceipt` carries the id used for post-effect verification. Compensation evaluation is permitted only when:

`execution_binding.invariant_manifest_id == manifest.manifest_id == verification_receipt.invariant_manifest_id`.

The manifest content itself is re-hashed during reduction, so a manually altered manifest id fails closed.

## Construction result

The exact publication candidate was executed once in the working directory and again after clean-copy reconstruction.

- `python -m py_compile outcome.py test_outcome.py`: PASS twice.
- `python -m unittest -v`: **33/33 PASS** twice.
- source changes between first and clean-copy run: **0**.

SHA-256 / Git blob identities of the tested bytes:

- `outcome.py`: 15,466 bytes; SHA-256 `4fd5a6001407b9e91ab3265aeca491643e035641f7926316ebf8835ba7b79449`; Git blob `680b104b28ba37633ec1031eac41c1945eb3aed9`.
- `test_outcome.py`: 16,139 bytes; SHA-256 `bd405d1ce6f07cbc0d08e00730f1bc24314f126dd38a224cc61c8effbae4fbf0`; Git blob `08a94d825976fcb534b9fde157c8f340cdc004c6`.

GitHub readback after publication matched both tested Git blob identities exactly.

## Key discriminator

The regression constructs an original pre-effect manifest requiring both:

- `primary == old`;
- `collateral == preserve`.

The command is bound to that two-invariant manifest. After a wrong effect and compensation, a hypothetical caller constructs a *new* primary-only manifest and a matching primary-only verification receipt. Reduction rejects the attempt because the executed command is still bound to the original manifest id. The post-effect shrink cannot authorize the old execution.

Other binding tests cover:

- same requirements in different order -> same manifest id;
- changed requirement value -> different id;
- changed scope -> different id;
- verification receipt from another manifest -> reject;
- cross-scope manifest substitution -> reject;
- tampered manifest id -> reject;
- duplicate/empty requirements and duplicate evidence -> reject;
- manifest without execution binding, or binding without manifest -> reject.

## Preserved v2 semantics

V2 outcome distinctions remain covered:

- stageable intended publication -> `PUBLISHED_VERIFIED`;
- pre-effect refusal -> `REJECTED_PRE_EFFECT`;
- direct intended effect -> `EFFECT_VERIFIED`;
- wrong direct effect without compensation -> `EFFECT_CONTRADICTED_UNCOMPENSATED`;
- wrong effect + clean compensation under the prebound manifest -> `EFFECT_CONTRADICTED_COMPENSATED`;
- missing/unverified/contradicted required invariant -> `EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE`.

Both complete and incomplete compensation preserve `effect_occurred=True` and the ordered wrong-effect history.

## H / T / D / C / U

**H.** Pre-effect binding of a deterministic invariant-manifest identity prevents post-effect requirement shrinkage from authorizing an already executed command.

**T.** Standard-library deterministic construction and unit regressions only; no live effect, model, GUI, game, network or user data.

**D.** `PASS_CONSTRUCTION_CANDIDATE_V3`: 33/33 tests pass on the exact clean-copy publication bytes, including post-effect shrink rejection and cross-manifest substitution rejection.

**C.** The execution binding is supplied as trusted evidence in this construction. V3 does not prove who minted it, whether it is durable, or whether a caller could omit a real invariant before execution.

**U.** No cryptographic signer identity, authenticated command channel, automatic dependency discovery, concurrency, crash/power-loss, external-service compensation, production ABI, latency or natural-rate claim.

## Next smallest question

Do not add another outcome label. The next integration question is whether one real caller/effect-owner boundary can carry the manifest id from plan/admission into the execution receipt and later verification without allowing adapters to replace it. That should be tested on a deterministic model-free path before any live/model allocation.
