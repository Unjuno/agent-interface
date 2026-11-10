# Win32 custody and late-input verification — 2026-11-10

## Scope

This verification covers the current worktree branch
`research/xvfb-autorepeat-release-frontier-20261110`, including the persistent
Win32 custody fence, old producer retirement, cancellation recovery, bounded
normal-completion observation horizon, and supervised MCP composition. It is
local code-level/native fixture evidence; it is not a live game or model trial.

## Conditions and commands

Host: Windows 11, Python 3.11. Worktree: this branch, 21 commits ahead of
`origin/main` with the changes listed by `git status --short` at verification
time. No GZDoom executable was found on PATH and no MAP01 GUI target was
launched. No runtime, model, or GUI application was downloaded.

Focused integration set:

```powershell
python -m unittest runtime.cli_v1.test_mcp_supervised_win32 runtime.cli_v1.test_mcp_supervised_backend_composition runtime.cli_v1.test_win32_supervisor_helpers -q
```

Custody/recovery set:

```powershell
python -m unittest runtime.cli_v1.test_owned_win32_session runtime.cli_v1.test_win32_custody_fence runtime.guarded_win32_v1.test_completion_observer runtime.guarded_win32_v1.test_operation_owner -q
```

Static checks:

```powershell
python -m py_compile runtime/guarded_win32_v1/process_cancellation.py runtime/cli_v1/owned_win32_session.py
git diff --check
```

## Results

- Supervised Win32/composition/helper set: 55 tests passed in 14.481 s.
- Session/custody/completion-observer/operation-owner set: 84 tests passed in
  5.018 s.
- Both static checks exited successfully.
- Follow-up normal-completion horizon boundary test: 5 completion-observer
  tests passed, including a deadline-incomplete horizon that remains unknown.
- Follow-up MCP delayed-input/recovery composition set: 25 tests passed in
  12.509 s, including delayed old-generation input quarantine and a producer
  blocked in the simulated `SendInput` path.
- `OperationCancellationSupervisor` now defaults helper startup readiness to
  5 s (was 2 s) after intermittent readiness failures at the 2 s boundary.
- When an input gate reached authorization-attempted/authorized, recovery
  requires proof the exact producer is gone and then discharges the owned
  recovery obligation even if emission evidence is absent or contradictory.
  Gates that never reached authorization can retain a verified not-dispatched
  path.
- Optional configured late-input horizon requires repeated neutral observation
  with consistent obligation readback, bounded inter-sample gaps, and full
  horizon coverage. Invalid, inconsistent, late, or sparse receipts leave the
  operation unknown/fenced rather than reporting success.
- A focused boundary case confirmed that when the horizon cannot fit before
  its absolute deadline, the completion result stays unknown instead of
  producing a successful completion receipt. The first test-harness attempt
  hung because its patched clock shared the module time object; that harness
  was corrected to use a deterministic monotonic sequence before accepting the
  passing result.

## Limits / next experiment

These tests establish fixture and local native boundary behavior only. They do
not establish physical input release during blocked platform I/O, successful
environment response, a MAP01 task effect, GZDoom behavior, a matched
latency/token/model-cost comparison, or broad reliability. The Windows host
had no discoverable GZDoom command, so the GUI experiment condition was
unavailable. Existing VizDoom MAP01 artifacts are separate trials and are not
counted as validation of this Win32 change.

README.md explicitly distinguishes pinned research dependency setup from
runtime, model/provider, and external GUI acquisition; that boundary was
reviewed and no implicit runtime/model/application download path was found in
the documented commands. This review is not a full audit of every installer
entry point.

### Runtime acquisition consent check

Inspected both `runtime/setup-golden-demo.sh` and
`runtime/setup-golden-demo-v3.sh`, their shared pinned requirements, and
`runtime/distribution_v2/build.py`. The setup scripts reject missing/unknown
flags before side effects, refuse to overwrite an existing venv, and only run
venv creation plus pip for pinned Python dependencies after
`--install-dependencies`. The zipapp builder reads the selected committed
source and writes local archive/manifest/checksum outputs; it has no package,
model, GUI, or container acquisition path. Existing tests passed on the host
that matches their required toolchain:

- WSL Ubuntu, dedicated Python 3.12.3: 4 `runtime.test_setup_golden_demo_optin`
  tests passed.
- Windows Python 3.11/Git: 21 `runtime.distribution_v2` build/validator tests
  passed.
- An initial Windows run of the shell-script tests failed because Windows had
  no `bash` executable; rerunning in WSL passed. An initial WSL run of the
  distribution tests failed because the Windows worktree `.git` pointer names
  `D:/ai57/...`, which WSL cannot resolve; rerunning on Windows passed. Neither
  environment mismatch changed source or test expectations.

### Separate WSL2 MAP01 expiry trial

On 2026-11-10, the retained VizDoom 1.3.0 environment and `map01-threat-contact`
fixture were reused in isolated Xvfb for a fresh expiry/release/rejection
trial. Owner release reached an empty X-server key state 0.670733 ms after the
lease deadline, the delayed forward submission was rejected, and late input
admissions were zero. The original program's release batch was
`confirmed_incomplete`; MAP01 exit and reward were false/zero. This is WSL2
X11 evidence and does not validate the current native Win32 branch. Full raw,
conditions, checksums, and limits are preserved outside this worktree at
`C:\Users\user\Documents\Codex\2026-10-03\new-chat-2\outputs\issue59-v39-expiry-live-20261110-a06`.

### Current combined Win32 regression run

On the Windows host, reran custody-fence, owned-session, completion-observer,
operation-owner, supervised-MCP, backend-composition, and helper suites
together after the horizon-boundary regression was added:

```powershell
python -m unittest runtime.cli_v1.test_win32_custody_fence runtime.cli_v1.test_owned_win32_session runtime.guarded_win32_v1.test_completion_observer runtime.guarded_win32_v1.test_operation_owner runtime.cli_v1.test_mcp_supervised_win32 runtime.cli_v1.test_mcp_supervised_backend_composition runtime.cli_v1.test_win32_supervisor_helpers -q
```

Result: **140 tests passed in 18.562 s**. On this Windows run the native named
mutex/separate-process admission fence, filesystem/registry ACL boundary, exact
old-producer identity retirement, delayed-input recovery composition, and
normal-completion horizon deadline case were exercised. This remains local
regression evidence, not a GZDoom or physical-keyboard trial.

### Persisted horizon-requirement bypass fix

The next audit found that `Win32CustodyFence.admit()` persists
`late_input_horizon_required: true`, but `resolve()` previously trusted its
caller-supplied flag (default false). The default call could therefore clear a
persisted unresolved fence with a release boolean but without horizon proof.
The new regression reproduced the bypass before the implementation change.
`resolve()` now compares the requested requirement with the persisted pending
requirement and refuses a mismatch; when the persisted requirement is true it
also refuses unverified horizon evidence. The full Windows regression command
above was rerun after the fix: **140 tests passed in 27.055 s**, followed by
`py_compile` of the changed Python files and `git diff --check`, both successful.
The new rejection case was also rerun by itself and passed. GitHub Issue #57
was rechecked and remains open; its integrated efficiency, broader reliability,
and MAP01 requirements remain unsatisfied by this Win32 work.
