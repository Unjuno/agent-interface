# Issue 7825 A01 source plan

Allocation `UNJUNO-7825-FSS-A01-20261005`; branch `research/7825-forward-secure-receipts-a01-20261005`; base `3f24e85bff32a93fbc1ca244f7f249b843710743`.

## Hypothesis and scope

A four-period synthetic receipt log can separate three properties: current-key compromise does not let the holder forge an earlier period under the tested key bindings; without a fresh external checkpoint, a valid current key can produce an alternate current suffix and the log verifier accepts a shorter valid prefix; a separately keyed checkpoint that pins the latest head rejects those alternatives. Correct signatures do not establish the truth of a receipt's semantic claim.

The forward-evolving fixture is a finite SHA-256/Lamport one-time-signature tree whose state frontier discards consumed leaves. The baseline uses independently provisioned period/slot one-time keys with a pinned public-key registry. Checkpoint signatures use a separate one-time-key registry. Each Lamport leaf signs one message in each test history; attack variants are isolated counterfactual branches.

## Test and decision

`setup.py` is construction-only: WSLc's CSPRNG creates ephemeral keys, builds four fixed records/checkpoints and emits the deliberately public current-period test compromise leaf. The fixture is saved and hash-frozen before the formal calls. The current leaf seed is an explicit synthetic attack input; no real secret is used. The full tree root seed, old leaves and witness private keys are not included in the fixture.

After freeze, invoke `candidate.py` once and `audit.py` once, each in the pinned, network-isolated, read-only-source WSLc container. The auditor reconstructs every output case without importing the candidate. No formal retry is permitted. Construction iterations are separately labelled and are not formal observations.

Expected finite outcomes: all original histories verify; current-leaf signatures do not verify as period-1 signatures; body mutation and interior deletion fail; current suffix rewrites and rollback to a valid prefix pass without a checkpoint but fail the latest-checkpoint gate; wrong-period and invalid-signature cases fail; missing/stale checkpoint fails; and an independently false but correctly signed period-2 claim remains authentic. A valid false claim demonstrates that signature/checkpoint authenticity is not effect truth.

The comparison decision is `NO_DISTINCT_HISTORICAL_FORGERY_ADVANTAGE_OVER_ROTATING_KEYS_ON_THIS_FIXTURE`: both key systems reject the same one tested historical forgery under their frozen registries. No performance, formal unforgeability, real secure-erasure, secure storage, monotonic-clock, witness-honesty, task-effect, runtime, GUI, model, input, or product claim follows. The implementation is a method fixture, not a standardized production FSS implementation or a security proof.

## Sources

- Bellare and Miner, [A Forward-Secure Digital Signature Scheme](https://cseweb.ucsd.edu/~mihir/papers/fsig.pdf), defines the intended fixed-public-key/current-secret-update/past-forgery boundary and conditions its construction on a hardness assumption and random-oracle model.
- Merkle, [A Digital Signature Based on a Conventional Encryption Function](https://people.eecs.berkeley.edu/~raluca/cs261-f15/readings/merkle.pdf), describes composing one-time signatures with a hash tree. These papers motivate the tested analogy; they do not validate this fixture implementation or its state deletion behavior.
