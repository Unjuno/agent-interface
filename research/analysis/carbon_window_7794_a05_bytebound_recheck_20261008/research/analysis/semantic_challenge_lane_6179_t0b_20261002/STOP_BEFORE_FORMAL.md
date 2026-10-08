# STOP before formal candidate — allocation 6179-T0B

Disposition: `STOP_BEFORE_FORMAL` (environment/source-provenance stop; not a scientific FAIL).

## Exact state

- Issue: [#6461](https://github.com/Unjuno/agent-interface/issues/6461), successor to #6179's unchanged `HOLD_METHOD_GATE_NOT_EXERCISED`.
- Branch: `research/semantic-challenge-6179-t0b-wslc-20261002`.
- Branch HEAD at stop: `18b2cd5ad5f6950ae6474e46eb1a53758f06832b`.
- Source tree was authored against and synchronized to main `18b2cd5ad5f6950ae6474e46eb1a53758f06832b`.
- Immediately before formal work, `git ls-remote origin refs/heads/main` returned `67ebd3016af9ed99a5cb40a39d4d753871f51d75`; the frozen source base was stale, so formal candidate must not start.
- GitHub MCP collision check before formal: no matching `6179-t0b` branch and no PR for #6461. Issue #6461 remained open.
- WSLc 3.0.1.0; cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; Python 3.12.14, linux/amd64.
- WSLc container inventory immediately before the construction test showed no running containers; host process scan showed no active WSLc run/exec owner. GPU was not requested or used.

## One-shot construction gate

Exactly one construction/test container was run, after the #5085 window ended. It ran `python -m unittest -v test_protocol` with the pinned image, `--pull never --network none --cpus 1 --memory 1G --user 65534:65534`, read-only source and fresh tmpfs output. Exit code 0; all 6 tests passed. The container was retained as exited (ID `736ce3a74111b322b9a8913b0f738ecb619453e4c4f346f53dc514c99f1cd738`).

The runtime emitted verbatim:

```text
wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.
```

The runtime did not expose evidence that the requested 1 GiB hard memory ceiling was enforced. Under the preregistered safety gate, this warning alone blocks candidate execution absent a positive enforcement check. The subsequent main advance is an independent source-provenance stop. Do not retry construction, candidate, or audit under this allocation.

## Invocation counts and evidence

- Construction suite: 1 invocation, exit 0, 6/6 tests.
- Candidate: 0 invocations.
- Independent raw audit: 0 invocations.
- Formal raw/audit outputs: none; no scientific result, PASS, or FAIL is claimed.
- No Docker/Podman, GPU, model, network access, GUI, live verifier, user data, or external effects.
- Candidate and auditor sources, tests, and preregistration remain preserved in this directory. #6179 history/result is unchanged.

## Required successor

Any future attempt requires a new successor allocation/Issue and fresh additive branch. First resolve the WSLc memory-limit observability/enforcement gate, then base the frozen source on a stable current main and verify it has not advanced at formal start. Keep the source construction test separate from candidate and raw-only auditor invocations; no retry of this allocation.
