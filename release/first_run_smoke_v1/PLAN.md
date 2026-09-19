# PH48 first-run launcher experiment v1

TASK: PH48-FIRST-RUN-SMOKE-20260915-01
BASE: ff2bbb5e200e2bf8ee2295ad97ca9dd0f158a371
BRANCH: release/first-run-smoke-ff2bbb5
Coordination: Issue #60, comment 5680783062.
Deadline requested by the user: 2026-09-17 (Asia/Tokyo). This is one
bounded contribution, not a declaration that the entire product is complete.

## Observation and minimum repair

At BASE, `runtime/README.md` documents direct execution of two v3 launchers,
but the Git tree stores both as `100644`. Change only their tree modes to
`100755`. Keep their blob IDs and frozen source bytes unchanged:

| File | Git blob |
| --- | --- |
| runtime/setup-golden-demo-v3.sh | 58f336f7010652503dad098c533dd42a80044d36 |
| runtime/golden-demo-v3.sh | ef489bbd68e3f80fac060b179fe90da2cce8d209 |
| runtime/golden_desktop_demo_v3.py (read-only) | 26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2 |
| runtime/requirements-golden.txt (read-only) | 4e46e2677aada41b5bf7433db18e1059592997f7 |

## H / T / D / C / U

H: On this POSIX container, both baseline direct entrypoints are rejected
before Python dispatch. Changing only executable metadata permits both documented
entrypoints to reach the intended doctor dispatch. This says nothing about
successful dependency installation or the real doctor's result.

T: Freeze this plan and the three Python sources in GitHub before running
`experiment.py`. The finite matrix is two entrypoints in baseline-then-repair
order, plus all 21 named unittest methods. Baseline cases check both direct exec
(EACCES) and bash invocation (126). Fresh disposable fixtures are used for each
matrix case. Unit-test subcases cover setup-stage failures and malformed pins.
No statistical sample, model call, GUI input or MAP01 allocation is consumed.
The experiment refuses an existing result directory and retains the first failure.

D: PASS only when all four pinned input blob hashes match, both baseline cases
fail before dispatch, both repaired cases dispatch to doctor, and all 21 tests
pass with zero skips. Any unmet predicate or execution error is FAIL and retained.
Non-POSIX environments are outside this claim; skipping tests is not a PASS.

C: A local chmod can conceal broken committed Git modes. Extraction can remove
permissions even when Git is correct. CRLF, missing files, a malformed Python
entrypoint, an absent interpreter, or setup-stage failure can invalidate the
first-run contract. These are explicitly tested; dependency/runtime failures are
not simulated into successes.

U: Source materialization uses exact MCP-fetched text and blob verification because
container GitHub DNS failed; it is not a full repository clone. Real bash and exec
run; Python/venv/pip/doctor dispatch is replaced by an isolated fail-closed double.
PATH contains only bash, dirname and that double. No package is installed and no
runtime is imported. No numeric confidence, latency, token, cost, native-Windows,
macOS, live-GUI or general-reliability claim follows.

## Authority and collision boundary

Only this new directory plus the two named executable bits are writable. Shared
runtime Python, workflows, site, root docs, DOOM recovery, conditional transport,
pending-effect and historical result lanes remain untouched. No coordinator
replacement, shared display, model/formal lease, automatic merge or direct main
push. Recheck current main for overlap before PR publication. Other agents may
review this branch and use the read-only preflight; they need not rebase their
frozen experiments onto it.

## Reproduction after the source freeze

```bash
python3 -m unittest discover -s release/first_run_smoke_v1 -p 'test_*.py' -v
python3 release/first_run_smoke_v1/preflight.py --root .
python3 release/first_run_smoke_v1/experiment.py \
  --source-commit FULL_SOURCE_FREEZE_SHA \
  --out artifacts-local/first-run-smoke-NEW-UNUSED-ID
```

The preflight checks only launcher/package boundaries. It neither launches a GUI
nor calls a model, and does not replace the existing v3 doctor. A checkout with
unstaged executable fixes still fails the committed-mode gate. A source archive
is labelled filesystem-only, never represented as Git-verified provenance.
