# Win32 supervised standard caller and task oracle R03

**Disposition: `PASS_SCOPED` for one owned fixture and one task.** This run
shows that the public supervised Win32 MCP path can carry one live target
generation through observation, static validation, dispatch, retained results,
and a server-configured task oracle that verifies one exact fixture effect.

The run used the frozen runtime source `5e378a416bd083609f1a9f5b4b9ade3fad9a584d`
with CPython 3.11.9 on the user-authorized local Windows PC. It created one
fixture. One public observation returned generation
`b4d1a16e633e437dbef35b77bdba2b54a5a68ee36c2daa693c92cb5d9e87f84e`, which the
validated program bound into its source. The exact program was dispatched once.
The first response was `pending` after the configured 10,000 ms wait; five
read-only `interface_results` calls for that same call ID then retrieved the
completed action. No input was replayed. The terminal producer receipt confirmed
all-up, the completion readback was neutral, and `recovery_required` was false.

The fixture independently wrote `{"clicked":true,"saved":true,"text":"task-oracle-r03-2c458ff912a7"}`.
The embedding server's configured oracle read that file and returned
`outcome=success` with the exact dispatch call ID, operation ID, and target
generation. The public response was `verified` with `task_success=true`. The
server returned `closed`, the fixture exited with code 0, and the original
foreground window was restored and confirmed.

Two earlier attempts remain failures and are preserved alongside R03. R01's
first harness invocation stopped before fixture creation because the harness
incorrectly required its pre-created empty output directory not to exist. The
second R01 invocation did start and cleanly close the fixture, but the MCP
server process failed during Windows multiprocessing bootstrap before MCP
initialization; no input was sent. R02 fixed that bootstrap issue. Its single
dispatch then returned `pending` after 5,000 ms; the fixture effect and producer
receipt show the click/save completed and terminal release was verified, but
the public task oracle was not called. R02 therefore remains
`FAIL_OR_UNKNOWN`; it was not retried. R03 uses a new attempt ID and token.

This is one deterministic fixture pass, not a reliability estimate. It does not
establish WSLc GUI behavior, blocked-platform-I/O release, cancellation recovery,
independent OS key-up observation, MAP01, matched efficiency, or transfer to a
real application. The server-configured oracle is application-specific and
reads the fixture's own effect file. WSL kernel hard-memory enforcement is
unrelated and was not measured by this native Windows run.

The frozen conditions and executable harness are in this directory. Raw MCP
responses, images, fixture events/effect, server receipts, and oracle evidence
are under `run/`. R01 and R02, including their failures, are retained in their
own sibling directories. The runner persisted protocol responses and server
receipts; the MCP SDK's console diagnostics were emitted to the parent process
and were not captured as a separate raw file. `SHA256SUMS` covers the complete
packet. After the live runs, the existing supervised Win32 composition and
owned-session local suites passed: 48 tests in 13.990 s under CPython 3.11.9
([record](local-validation.json)). Its `SHA256SUMS` file covers every other
file in the R03 packet.
