# Construction iteration log — pre-freeze, not formal T0 evidence

## Attempt 01 — mutation-control smoke (2026-10-05 14:48 JST)

- Runtime: WSLc 3.0.1.0; cached
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
  (Python 3.12.14); `--network none`, source mounted `:ro`, 1 CPU,
  requested 128 MiB; container used `--rm`.
- Command: `wslc run --rm --pull never --network none --cpus 1 --memory 128M
  --volume "C:/Users/junny/Documents/Codex/m7993/research/analysis/verifier_maturity_censoring_7993_a01_20261005:/src:ro"
  --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
  python -B -m unittest -v test_protocol`.
- Outcome: container exit 1; 5 tests ran, 4 passed, and
  `test_raw_only_audit_and_ten_effective_mutations` failed because one test
  mutation assigned `"0"` to an estimator already equal to `"0"`. This was an
  ineffective/no-op mutation, not a candidate scientific counterexample.
- The WSL kernel emitted: `Your kernel does not support swap limit
  capabilities or the cgroup is not mounted. Memory limited without swap.`
  Therefore the requested memory flag is not evidence of an effective hard
  limit. No formal candidate/auditor process pair was run, and no source freeze
  or scientific disposition was produced by this construction attempt.
- Correction: change the mutation's replacement value to `"1/2"`, making it
  differ from the expected zero estimate for mask 14. Preserve this first
  failure; subsequent construction checks remain distinct from the one frozen
  formal T0 invocation.

Output excerpt (exact test outcome):

```text
test_all_sixteen_independent_masks_and_exact_ht_expectation ... ok
test_complete_case_undercoverage_witness_and_safe_bound ... ok
test_delayed_resolution_and_horizon_statuses_remain_distinct ... ok
test_raw_only_audit_and_ten_effective_mutations ... FAIL
test_zero_support_and_hidden_misspecification_are_not_guarantees ... ok
Ran 5 tests in 0.058s
FAILED (failures=1)
```

## Attempt 02 — corrected mutation-control smoke (2026-10-05 JST; time not captured)

- Runtime and isolation were unchanged from Attempt 01: WSLc 3.0.1.0, the same
  cached Python 3.12.14 image digest, network disabled, source read-only, one
  CPU, requested 128 MiB, and `--rm`.
- Command: `wslc run --rm --pull never --network none --cpus 1 --memory 128M
  --volume "C:/Users/junny/Documents/Codex/m7993/research/analysis/verifier_maturity_censoring_7993_a01_20261005:/src:ro"
  --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
  python -B -m unittest -v test_protocol`.
- Outcome: exit 0; all five tests passed, including all ten effective mutation
  controls. Host-captured stdout was empty (0 bytes; SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`);
  stderr was 1,031 bytes (SHA-256
  `bb052307fc3467835636bacad070f14e240a1ca98b25105abde3165eb4c567da`).
  Stderr contains unittest output and the same kernel warning that cgroup swap
  limits are unsupported/unmounted, so the requested memory limit is not
  treated as proven enforcement.
- The immediately-following host memory snapshot reported 232,008 KiB free.
  This was a construction test only: no candidate/auditor formal pair ran and
  no scientific disposition was produced. The failure in Attempt 01 remains
  preserved above.
