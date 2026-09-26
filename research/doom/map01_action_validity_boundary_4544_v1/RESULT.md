# Result — action-validity timestamp boundary (construction-only)

Classification: **`FAIL_GUARD_LOCAL_FAIL_CLOSED_BOUNDARY`**.

## H/T/D/C/U and result

- **H:** An inverted controller-decision/capture pair should produce a
  fail-closed guard receipt (authority false, invalidation retained, new
  decision required). **Not supported** by this v1 local state-machine
  boundary.
- **T:** Four deterministic synthetic cases were executed against the exact
  current-main v1 guard: ACTIVE decision after capture, ACTIVE equality, ACTIVE
  decision 1ns before capture, and BETWEEN decision 1ns before capture.
- **D:** The two non-inverted controls returned `INPUT_ACTIVE` as expected.
  Both 1ns-inverted cases raised
  `ValueError: controller decision precedes current snapshot`, not a receipt.
  After the ACTIVE exception, the guard still reported
  `INPUT_ACTIVE`, `current_input_authority=true`, and no invalidation.
  After the BETWEEN exception, it remained
  `BETWEEN_PROGRAMS_REQUIRES_FRESH_CHECK`, authority false, and no
  invalidation. The local guard contract gate therefore failed.
- **C:** This is deterministic construction evidence only. It is not a
  production safety-failure finding: in consumed formal allocation 990641 the
  exception escaped the runner, and the retained record independently reports
  29/29 verified-empty owner releases. We did not catch the exception and
  continue in the formal runtime. No source/runtime modification, model, game,
  GUI, motor input, or formal allocation was used here.
- **U:** The exact operands/domain in seed 990641 remain unlogged; this probe
  does not establish that the formal event had a 1ns inversion or explain its
  cause. Whether outer teardown and verified release hold for every integrated
  caller is unknown.

## Reproduction and provenance

Main base: `a778bdd577b149a5ec964bbe19da533311335e2f`.
Container: OrbStack context; cached
`issue2679-map01-runtime:20260921-pinned`,
`sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`,
`linux/arm64`. Commands used `--pull=never --platform linux/arm64
--network none --read-only`, a 16 MiB no-exec tmpfs, and a read-only source
mount. The image has ENTRYPOINT `python runner.py`; the experiment explicitly
overrode it with `--entrypoint python`.

The main-branch source blob IDs are:

- `action_validity_admission_v1.py`: `31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e`
- `running_action_guard_v1.py`: `d54047e78bc76f53ef47c6f70fd4a3be6318f09c`
- `test_running_action_guard_v1.py`: `a4a423da1118f2da8cca08e9965419fac322461a`
- `test_action_validity_admission_v1.py`: `9d5dbf119fcb56c75ac1732da60b18832876e1a5`

The exact files were fetched from main via GitHub MCP and staged outside the
shared checkout. The current-main existing unit suites plus this experiment's
replay and audit/corruption tests passed **19/19** in the pinned container. The
independent stdlib audit accepted all four retained cases and confirmed the
observed FAIL classification. A prior test-harness attempt imported a same-named scratch
module and failed the replay comparison; the harness was corrected to import
the sibling experiment by its exact path, then the final 19-test run passed.
The image-entrypoint mismatch on the first exploratory invocation is also
resolved by the explicit entrypoint override.

Reproduce from repository root after merge:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=research/live_control:research/doom/map01_action_validity_boundary_4544_v1 python3 -B research/doom/map01_action_validity_boundary_4544_v1/experiment.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=research/live_control:research/doom/map01_action_validity_boundary_4544_v1 python3 -B -m unittest -v test_running_action_guard_v1 test_action_validity_admission_v1 test_experiment
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=research/live_control:research/doom/map01_action_validity_boundary_4544_v1 python3 -B research/doom/map01_action_validity_boundary_4544_v1/audit.py
```

The executed pinned-container invocation used the same immutable source bytes
and module import path from a disposable staged root (no shared repository
checkout):

```sh
docker run --rm --pull=never --platform linux/arm64 --network none --read-only \
  --workdir /study/research/doom/map01_action_validity_boundary_4544_v1 \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --entrypoint python \
  -e PYTHONPATH=/study -e PYTHONDONTWRITEBYTECODE=1 \
  -v /tmp/map01-clock-boundary.GyOduI:/study:ro \
  issue2679-map01-runtime:20260921-pinned \
  -B -m unittest -v test_running_action_guard_v1 test_action_validity_admission_v1 test_experiment
```

No fresh formal seed was frozen or invoked. The next formal attempt must be a
new allocation with exact current-snapshot and controller-decision operands
persisted before acceptance decisions; this result alone does not authorize
such an allocation or a runtime patch.
