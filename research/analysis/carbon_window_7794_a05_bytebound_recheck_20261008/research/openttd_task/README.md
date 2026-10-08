# Visible OpenTTD saved task and read-only observer — 2026-09-13

A road-placement fixture can now be saved and restored in fresh private X11
processes with its target visible. The observer restores the task coordinates
from GameScript save data and issues no world-construction commands. This is
preparation for actual shared-interface pointer use, not an agent success or a
formal benchmark adoption.

## Task and restored evidence

The intended task is to join signs **A** and **C** with the straight three-tile
road, owned by the player's company. The adjacent three-tile row marked **X**
must remain without roads. The contract covers target tiles 678–680, forbidden
tiles 742–744, and the two bidirectional adjacent connections. It uses the
previously [calibrated scorer](../openttd_oracle/README.md).

The canonical fixture is
[`results/cohort-03/baseline.sav`](results/cohort-03/baseline.sav), SHA-256:

`7836587d28056c534dd3ce2968fc89d3e9b47e28400afc90234954a470f8e97c`

In the final cohort:

- Setup exported the six empty tile states and two disconnected edges, placed
  the signs, centered the viewport through the setup console, and saved.
- Two fresh HOME/XDG/Xvfb/Openbox/game processes loaded those exact save bytes.
  Each produced an initial restored observation and two subsequent observations;
  all six matched the setup's task fields. The scorer correctly reports the
  initial task as unfinished in all observations.
- Original-resolution screenshots from both restored processes show A, C and
  X in the initial viewport. This was visually inspected; it is not an automated
  semantic screenshot assertion or evidence of any road built by an assistant.
- An additional fresh unsaved game with the observer package refused startup
  with `saved contract required` and emitted no task observation.
- The input save hash was unchanged before and after each process. All owned
  processes were reaped. The experiment still uses forced termination when
  OpenTTD does not exit on SIGTERM; it does not establish graceful-exit reliability.

See [audit output](results/cohort-03/audit.json). There were nine launches across
three development cohorts, including the first failed setup and an intermediate
save/restore cohort whose viewport did not show the target.

## Setup, observation and controller boundaries

`setup/` contains the only world-mutation calls: sign placement on a selected
flat/buildable rectangle. It does not build roads. Its save callback serializes
the selected coordinates. Setup console commands use the historical XTEST
keyboard driver to center the view and save; these commands are fixture
preparation, not assistant task actions or shared-runtime coverage.

`observer/` has a separate entry point. It requires a loaded saved contract,
then reads tile ownership/road state and directional adjacency. Its company
and road-type calls set query context; its Save/Load callbacks serialize script
metadata. Source inspection finds no sign/road construction, viewport movement,
game pause or other world-mutation call in this observer package. This is an
audited small source boundary, not a hardened engine API capability sandbox.

The packages deliberately register the same GameScript name/version so the
saved metadata can be read by the observer implementation. They are distinct,
source-hashed setup/observer artifacts in the manifest; do not describe this as
one identical script across phases. Only the observer belongs in the subsequent
controller phase. The setup package must not be used to reload the canonical
fixture: its Start method chooses and initializes a scenario again.

## Preserved failures and corrections

1. `cohort-01` / `run.py`: setup reached readiness, but the harness could not
   find its expected save filename. OpenTTD 13.4's console appends `.sav`
   unconditionally; the request already included that suffix. No error-time
   screenshot/file listing was captured in this first version, so no claim is
   made about the exact file created before temporary-directory cleanup.
2. `cohort-02` / `run_v2.py`: removing the supplied suffix produced a loadable
   save; two restores and the unsaved rejection check worked. The target was
   outside the viewport. State equality alone did not make a usable visual task.
3. `cohort-03` / `run_v3.py`: setup explicitly ran `scrollto 679` before saving,
   and the window resolution was fixed at 1024x720. Both restored views show the
   task signs. This is the selected fixture. Earlier source/results are retained.

Console behavior was checked against the
[OpenTTD 13.4 console source](https://github.com/OpenTTD/OpenTTD/blob/13.4/src/console_cmds.cpp).
Save creation is accepted by the runner after stable nonzero file size; the
stronger evidence is successful loading by two independent game processes.

## Limits and next experiment

These are short observations of one saved scenario. They do not prove full-world
or trajectory determinism, reset after actual held-input interruption, robustness
under repeated crashes, or reliable operation over long sessions. The oracle
checks only its declared six tiles; destruction elsewhere is outside this task
contract. Engine version and assets reuse the prior pinned Ubuntu 13.4/OpenGFX
environment; this runner pins script/session sources but does not independently
rehash the installed engine binary on every launch.

The actual controller has not been connected. Shared pointer position/button,
drag and wheel semantics still need the same focus, stale-observation, deadline,
cancel and input-release invariants as keyboard actions. The next experiment is
to use this fixture for that shared path and actual assistant operation, followed
by fresh task/window positions and cancellation/recovery cases. A three-tile
placement smoke is not the eventual dense-GUI/long-horizon benchmark.

No speed, same-model token, human-tempo or freeze qualification claim follows
from these preparation runs. DOOM and ordinary desktop coverage remain required.

## Reproduce

Use the private Linux asset prefix described in
`research/benchmark_discovery/REPRODUCE.md`. From the repository root:

```sh
python3 research/openttd_task/run_v3.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/openttd-task-rerun
python3 research/openttd_task/audit.py /home/taka/openttd-task-rerun
```

The runner rejects an existing output directory. A freshly generated save may
differ in full bytes from the canonical fixture due to save timing; each cohort
must compare restores of its own unchanged save. To audit committed evidence:

```sh
python research/openttd_task/audit.py research/openttd_task/results/cohort-03
```
## Follow-up: shared pointer self-use

The preparation above is followed by [one successful visual self-use episode](SELF_USE.md)
through the shared pointer candidate. Its scope, independent score, measured
intervals and unresolved qualification gates are recorded separately.
