# Observational-equivalence proof

## Claim
Let two hidden histories differ only in producer identity: one is HUMAN and one is EXTERNAL_PROCESS. Let the classifier receive only the declared provenance-free observable record (event family, target/effect class, timing bucket, focus state, changed-state digest class). If the observable records are identical, every deterministic classifier must return the same output for both histories. Therefore it cannot correctly return HUMAN for one and EXTERNAL_PROCESS for the other.

## Argument
1. A deterministic classifier is a function of its verifier-visible input only.
2. The paired histories are constructed to have byte-identical verifier-visible inputs.
3. Equal inputs to a deterministic function produce equal outputs.
4. The hidden ground-truth labels of the two histories are different.
5. A single equal output cannot equal both different ground-truth labels.
6. Therefore any classifier that emits a specific HUMAN or EXTERNAL_PROCESS label is wrong for at least one member of every indistinguishable pair.
7. Returning UNATTRIBUTED makes no false specific actor claim. It deliberately declines an unidentifiable distinction.
8. Adding a correctly bound trusted actor witness changes the observable input and can therefore make the two histories distinguishable; this is outside the provenance-free premise.

## Residual empirical question
Whether a real OS/device/broker provenance source is trustworthy, available, privacy-acceptable, and low-overhead is empirical and not decided here.
