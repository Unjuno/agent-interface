# Post-score late-usage measurement composition

This frozen synthetic experiment checks the current-main chain from a timeout
generation through `RecordedPublicMcpCaller.observe_late_usage`,
`ProviderAttemptRecorder`, and `build_measured_run`. One positive case supplies
one hash-bound App Server usage row after an independent UNKNOWN task score; a
matched control supplies no row. Neither case uses a provider, Relay, target
application, or OS input.

The source pin and decision rule are in `conditions.json`. The implementation
files in the pin are read-only; the experiment code lives only in this packet.

Run from this directory with Windows CPython 3.11:

```powershell
py -3.11 -m unittest -v test_composition
py -3.11 -O -m unittest -v test_composition
py -3.11 run_experiment.py
py -3.11 audit_packet.py
```

`run_experiment.py` refuses to overwrite `runs/`. The audit revalidates each
measured record, checks retained recorder raw hashes, and compares all six
source files' Git-clean-normalized worktree blob IDs with the frozen Git
revision (so Windows CRLF checkout conversion does not create a false source
drift). It also excludes Python's ignored `__pycache__` bytecode from the
packet file-set check. The `.gitattributes` control file is checked for the
raw-byte preservation rule directly; it is excluded from the SHA256SUMS file
set because Windows may convert its line endings on checkout. This experiment
does not establish
provider billing, task effect, matched A/B/C economics, or recovery reliability.
The required `effect_attribution` envelope is synthetic schema scaffolding:
effect time is null, task success is UNKNOWN, and its times do not assert an
input release or a real authority boundary.
