# V39 release projector exact-integer boundary

## H — hypothesis

The release measurement projector must reject JSON booleans wherever its schema requires integer ordinals or step identifiers. Python equality makes `True == 1`, so equality-only checks can incorrectly mark malformed release evidence as measurement-ready.

## T — bounded test

- Baseline freeze: current main `19a6b723e58ccfd2b8265e88659589ef9223fcc9`.
- Baseline projector Git blob: `3683534757f55cbc2c60b1ce2cde7a0847c3f090`.
- Existing fixture/test blob: `28e34663420af31642f8826f0f53385327872be6`.
- Fixed candidate: PR head `b2137ef3373ce08c148a6af43cbee422fa7aed05`.
- Candidate projector blob: `21ad65857a22c3f713a8f38fec738598584abb64`.
- Candidate tests blob: `eb67c2240653384aae1071b0ddf7c2551b68e52e`.

Two controlled corruptions were tested against the real `project()` implementation and existing fixture: boolean `server_keyup_attempts[0].attempt`, and boolean release `step` / `release_batch_step`. Before the production guard, each returned `measurement_ready=true`; each added regression failed at the explicit `assertFalse` with `AssertionError: True is not false`. The independent contract oracle is exact JSON/Python typing: each ordinal/step must satisfy `type(value) is int` before its expected integer value is compared.

## D — observed result

The projector now checks exact integer type for retry ordinals, release identity steps, and release batch steps before equality. Valid integer fixtures remain accepted. Both malformed controls are rejected. The seven focused tests pass normally and under optimized Python; compilation passes.

Commands:

```sh
python -m unittest test_project_v39_release_measurement_v1 -v
python -O -m unittest test_project_v39_release_measurement_v1 -v
python -m py_compile project_v39_release_measurement_v1.py test_project_v39_release_measurement_v1.py
```

Both unittest runs: `Ran 7 tests`, `OK`. The regression methods are `test_rejects_boolean_attempt_ordinal_that_aliases_one` and `test_rejects_boolean_release_step_aliasing_integer_one`.

## C — controls and scope

This is synthetic schema-boundary verification on the host. It does not exercise X11, native input, a game, a model, a container, or a formal allocation. It establishes no physical key release, application consumption, live latency, threat response, task effect, or MAP01 outcome. The exact-source tests and test-first counterexamples are author-executed; separate reviewer scrutiny is requested on [PR #8134](https://github.com/Unjuno/agent-interface/pull/8134).

## U — unresolved

PR #8134 remains Draft pending review and applicable repository gates. The broader #59 current-main threat exposure and per-key/live measurement work remain open.
