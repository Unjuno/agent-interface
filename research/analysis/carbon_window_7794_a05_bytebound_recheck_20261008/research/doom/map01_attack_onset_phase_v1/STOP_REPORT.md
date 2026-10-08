# Issue #4223 formal execution stop

## Disposition

The single frozen formal orchestration was started once and stopped in its first scheduled case, `p1-immediate` / `IMMEDIATE`, before the initial observation. The retained frozen runner result is `FAIL_FORMAL_RUNTIME_OR_SCHEMA`, with zero completed rows, `formal_invocations=1`, `reruns=0`, `replacements=0`, and `tuning_after_freeze=0`. No physical input edge, scorer sample, or gameplay result was produced. This is an environment/runtime stop, not a scientific PASS, HOLD, or gameplay FAIL.

Do not rerun this frozen allocation. Any further execution requires a fresh successor identity, a corrected and verified environment, a new freeze, and its own single-run budget.

## First failure

The first session's child process closed stdout while importing the retained source chain:

`session_entry.py → doom_retained_input_backend_v3 → doom_typed_coast_backend_v1 → coast_backend_v1 → session_v10 → session_v9`

At `session_v9.py:4`, Python raised `ModuleNotFoundError: No module named 'Xlib'`. The exact offline runtime artifact includes `wheels/python_xlib-0.33-py2.py3-none-any.whl` (SHA-256 `c3534038d42e0df2f1392a1b30a15a4ff5fdc2b86cfa94f072bf11b10a164398`), but `DOCKERFILE.local.formal-stop` omitted it from its offline pip install list. This is a container assembly defect. The exact retained formal result and first-case launch/controller files are preserved unchanged under `formal/`.

## Scope and integrity boundary

- The frozen H/T/D/C/U plan, source capsule, seed, schedule, arms, timing, scorer, and decision thresholds were not edited.
- Runtime artifact 10398313098 was downloaded and its 2,592 source files matched the embedded manifest: missing 0, hash/size mismatches 0. The manifest explicitly says `experiment_executed=false`.
- The v12 `input_owner_v12.py` and `adapter_contract.py` matched the preregistered SHA-256 values (`b63e8a…6c1508` and `ed7e4f…9badf` respectively).
- The actual research container was `linux/amd64` under OrbStack on an arm64 host, Python 3.13.5. It had no network, a read-only root filesystem, read-only source mounts, and a bounded writable output mount.
- The raw controller event list is empty; no `runtime/` directory or session observation exists for the first case. The remaining seven sessions were not launched.
- The frozen success auditor cannot audit a zero-row runtime as a scientific result. This report is a bounded stop audit only; candidate/auditor agreement and scientific corruption-control gates were not reached.

## H/T/D/C/U outcome

- **H:** Not tested; no observation or attack occurred.
- **T:** Partially instantiated from the frozen offline source/wheels in the local OrbStack container. The missing `python-xlib` dependency invalidated runtime readiness before science.
- **D:** Not evaluable. Retained machine decision: `FAIL_FORMAL_RUNTIME_OR_SCHEMA` at the first case.
- **C:** No phase/timing inference is possible.
- **U:** No efficacy, task-effect, MAP01, model, latency, population, or production claim.

## Reproduction of the retained stop

The frozen execution command is recorded in `FORMAL_EXECUTION_ENVIRONMENT.json`. The local image recipe is retained as `DOCKERFILE.local.formal-stop`. Rebuilding it and invoking the formal runner would start a new execution, so these files document provenance only and are not instructions to rerun this allocation.
