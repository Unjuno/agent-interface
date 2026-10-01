# First-run smoke gate

Run before the existing golden desktop setup, from the repository root:

```bash
python3 release/first_run_smoke_v1/preflight.py --root .
```

The check is read-only. It does **not** install dependencies, open a display,
import the runtime, call a model, or run the demo. Exit 0 means
`PASS_LAUNCHER_BOUNDARY`, not a working GUI installation. Exit 1 means a
boundary check failed. `--out NEW.json` retains a new report and refuses to
overwrite an existing one (exit 2).

It checks both committed Git modes and actual filesystem execution permission,
exact worktree/HEAD bytes, LF bash shebangs, required entrypoint syntax and exact
nonduplicate dependency pins. It labels archives without `.git` as
`archive_filesystem_only`. The check does not establish full import/dependency
closure, compatible package wheels, credentials, or supported GUI hardware.
Native Windows execution is outside this POSIX launcher contract.

## Concrete fix

The v3 setup and launcher scripts were mode `100644`, although the documented
commands use direct `./runtime/...` invocation. This change makes only those two
Git entries `100755`; their contents and Git blob IDs are unchanged. Older v2
entrypoints, runtime semantics and historical research artifacts are untouched.

See [the frozen experiment plan](PLAN.md) and, after execution, the retained
report in this directory. Tests use real bash/exec but replace Python dispatch
with a fail-closed local double. A passing dispatch test is not evidence that
real pip installation or the golden desktop doctor passed.

## Deadline integration boundary

For the 2026-09-17 target, the release owner's remaining acceptance checks are:
run the real setup and doctor on the **claimed supported host**, retain one fresh
user-like golden workflow and its independent audit, and publish that exact
runnable artifact with its limitations. This task does not launch or authorize
that fresh model/GUI workflow. Do not advertise native Windows, macOS or broad
reliability from this smoke result. Prefer one honestly reproducible demo over
additional unvalidated platform claims.

This PR is separate from DOOM recovery, image transport, pending-effect, shared
runtime and site work; the two launcher mode changes do not alter source hashes
of another agent's frozen runtime experiments.
