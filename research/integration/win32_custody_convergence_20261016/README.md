# Win32 custody: current-main convergence of PR #6934

2026-10-16. Base `96820f2ba8de458f12ffa710a4ec18e6edfa12c6`.
Zero-state repair `59493fdea3273e00b04a4618885cf254e25c0ae0`; final tested
code `75e13709f00cdc9f350b531941a191aaa1cf945b`.
This is inert/local construction, not native Windows qualification.

## Preserve the proposal without reverting newer main

Old draft [#6934](https://github.com/Unjuno/agent-interface/pull/6934) remains pinned
at `b332fddcd1372e0cbba07c50691c215b20bd5831`. Its 184 historical evidence paths
are already exact Git-blob matches in main. Do not copy them again or rewrite
their original results. The dated rescue notes correctly describe their earlier
evidence-only transfer; this separate record describes subsequent integration.

| Original proposal responsibility | Current-main disposition |
|---|---|
| Private journal/observation/admission/effect/terminal custody | Already integrated through `0681b39940` and subsequent repairs. All seven original core custody test modules (42 methods) pass in the selected current suite. |
| Retain key/button release on ambiguous zero, deduplicate physical VK aliases | Newly connected to the current backend, retaining its newer guarded-target APIs, Unicode custody and owned Win32ExecutionError evidence. |
| Refuse task input through a replacement session while backend custody remains | Newly connected after core admission and before native preflight; guarded BoundView forwards backend ledger state. Release-only cleanup remains available under its existing contract. |
| Stop following effects after unverified explicit UP | Preserve main's stronger exception-and-cleanup path; do not replace it with the old loop. |
| Historical code/source/raw/archive evidence | All 184 original paths unchanged. The old branch is retained; historical test/native/runtime images are not promoted to current qualification. |

The old head would delete newer capture/bound execution features and roll back
later compiled cancellation/observation/literal repairs. It is superseded by the
current composition after this repair is integrated, rather than merged wholesale.
This resolves a finite proposal; #57/#59 and Windows readiness remain separate.

## Source-first failures and current behavior

The first five-method RED reproduces a zero-state release reporting verified,
clearing tracked custody and returning session completed. The replacement-session
RED then attempts a DOWN at the inert API despite pending backend custody; that
UP-only fixture rejects it before changing state. The BoundView RED shows its
pending ledger was hidden from the ordinary session gate. All three first controls
remain retained.

The repair distinguishes reported down, nonzero observed up and unknown zero.
Release retries keep unknown key/button obligations, use one send/query per
physical key alias set, and return explicit unknown lists. Explicit unknown UP
refuses later effects. Existing session recovery makes one cleanup attempt,
remains required under zero, and clears only on verified release; it never reports
task success or replay permission. This is within one backend object's custody,
not durable authority across new backends/processes or concurrent constructors.

Microsoft documents zero for API failure as well as a possible up-state result:
[GetAsyncKeyState](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getasynckeystate).
The nonzero low-bit fixture is a successful-up witness, not a prediction that a
healthy desktop always returns one. Four old healthy fixtures now supply that
witness; new zero controls preserve the distinct unavailable case. This can hold
indefinitely on genuine healthy zero. No availability witness, usability promotion,
physical release deadline, live task effect or efficiency gain is claimed.

## Executed validation and containment

Normal and optimized selected suites each pass **112 methods, zero skips**:
seven new unknown/custody methods, existing inert Win32 helper/session tests,
seven core custody modules and eleven guarded Win32 modules. The actual native
`Win32IntegrationTests` class is explicitly excluded, not silently counted as a
pass or skip. Backend construction and ctypes.WinDLL are forbidden by the runner.
Owned Python pixel-verifier/cleanup peers use synthetic images and do not invoke
native Windows input or a provider.

Initial expanded runs exposed healthy-zero fixture assumptions, one missing
BoundView connection, and one Unicode fixture assumption. These failures and
repairs are retained. During checkout expansion an uncommitted BoundView edit was
restored away; it was reapplied before the final source was committed and tested.
Legacy guarded tests write JSON/images to cwd. Their first generated 231 files
were hash-verified and preserved externally; final runs use separate external
directories per mode. Their complete resulting synthetic artifacts and stdout/
stderr are retained under `normal`/`optimized`. No historical producer was rerun.

`MANIFEST.json` records original/main evidence joins, Git and tested worktree
source hashes separately, AST equivalence where line-ending normalization differs,
run outcomes and packet hashes. The source tests remain in runtime; the separate
runner selects inert classes and prevents accidental native fixture execution.

Reproduce with Pillow installed and the relevant committed tests materialized:
set `PYTHONPATH` and `AGENT_INTERFACE_TEST_REPO` to the repository root, use a fresh
external working directory, and run `python check_win32_custody_isolated.py` (or
`python -O ...`). This produces synthetic local files; it allocates no GUI, game,
provider, WSL or container resources.
