# #5081 v6 — host zero-fit construction report

**Disposition:** `PASS_CONTRACT_FIXTURES_ONLY`; not a Docker construction PASS,
formal result, scientific result, or authorization to use the shared container.

## H/T/D/C/U

- **H:** a fully realized Docker token array can be checked by exact equality,
  and an online-feedback claim can be gated on new feedback arrival/consumption
  plus an optimizer interval overlapping an active System-1 inference window.
- **T:** allocation `needle-role-skill-joint-retention-20260928-v6`, branch
  `research/needle-role-skill-joint-retention-v6-20260928`, base main
  `708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`. The test runs only the standard
  library `unittest` suite in `test_protocol.py`; no model, optimizer, formal
  seed, image, or Docker command is invoked.
- **D:** 8/8 host unit tests pass. The suite covers exact argv equality and
  rejects token splitting, omission, additions, reordering, mount-format
  mutation, path aliasing, and missing directories. Event fixtures accept a
  feedback update that starts after an in-flight query starts and overlaps its
  inference-call interval (not merely a broad query window); they reject
  early/late feedback, non-overlap, a wait-only query window, shared worker
  identity, missing query evidence, and malformed/empty records.
- **C:** only temporary directories and synthetic integer timestamps are used.
  The Docker command contract explicitly pins `--entrypoint=python`, one exact
  `--network=none` token, image digest, mount tokens/order, environment, and
  runner arguments. No host shell string normalization is involved.
- **U:** these unit fixtures verify the validator, not actual Docker argv
  execution, container/image entrypoint metadata, independent OS process
  scheduling, live arrivals, model updates, latency, role retention, or
  scientific thresholds. Formal work remains behind the coordinator release
  gate. No result from v5 is changed or upgraded.

## Exact verification

Environment: Windows 10 build `10.0.26200`, CPython `3.11.9` (64-bit AMD64).

Command, run from this directory:

```text
python -B -m unittest -v test_protocol.py
```

Final outcome: `Ran 8 tests in 0.009s` / `OK`. `git diff --check` also passed.
The first run exposed a contract exception-type/message mismatch for a missing
output mount; the API was made consistently fail-closed with `ValueError`. An
additional test then caught a fixture that accidentally overlapped inference;
its call interval was corrected so the negative control is genuinely
non-overlapping. The final eight-test run passed. Both construction defects and
repairs are retained here; no optimizer or container was involved.

## Resource and allocation boundary

The formal issue #5081 remains queued. #5085/#5144 still require the owner of
the unrelated OrbStack container to confirm terminal state and the coordinator
to record an exact lane release. An empty Windows Docker inventory is not a
lease. This report does not claim Docker availability was tested and makes no
Docker invocation. The seeds in #5081 are not consumed by this construction
suite.
