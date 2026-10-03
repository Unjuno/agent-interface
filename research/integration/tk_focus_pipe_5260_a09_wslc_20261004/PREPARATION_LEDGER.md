# A09 preparation evidence (not a scientific allocation)

The original A02–A08 frozen sources and results are unchanged. This directory
contains an unfinished A09 draft. app.py now publishes through FocusPipe;
candidate.py and fixture.json now contain their A09 draft derivation; an independent
auditor is not connected. No A09 GUI/input experiment has been executed or frozen.

## Test-first transport and gate

- Four new PipeSession tests initially failed because the session was absent.
  Implementation then passed the entire draft suite: 45 tests on Windows.
- Four gate tests initially produced two assertion failures and two test-access
  errors. Missing-field accesses were guarded so the intended missing behaviors
  were observed as four assertion failures. Implementation then passed all 49
  draft tests on Windows.
- Gate tests use real OS pipe bytes, not mocked receipt transport. They exercise
  fresh receipt admission, latest FocusOut overriding an older FocusIn, retention
  of the first empty-pipe sample, and early refusal at actual EOF.
- The Linux-only characterization adds a real Popen child with pass_fds containing
  only the writer. It checks the PC_PIPE_BUF bound, exact receipt bytes decoded by
  the parent, separate stdout `RESULT`, empty stderr and actual EOF. This test
  validates existing transport integration; it is not a GUI/first-character test.

## Actual Linux unit run

Executed once using WSLc and cached image
`sha256:217851fe68e7340cd6301e6d1a1bd79d2c7b6cb4d13eb444a06fabaf0fde3417`.
Container name: `ai-5260-a09-pipe-unit-20261004-01`.
Source bind read-only at /src; uid/gid 65534:65534; network none; pull never;
requested CPU 0.5 and memory 512M; /usr/bin/python3 -B -m unittest discover -q.
Exit code 0; 50 tests ran in 0.083 seconds and passed. The container was run
with --rm. No DISPLAY, Xvfb, XTest, application click, key, Save, model or GPU
operation was invoked by this unit command.

Original runtime warning:
`wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.`

Resource options are requests, not proof of effective limits or improved memory
behavior. The reported unittest duration is not a performance comparison.
This run does not establish focus admission efficacy or satisfy the ten-app
candidate/auditor allocation in PLAN.md.

## Producer and app callback connection

Three further tests were observed failing before their respective implementation:
actual publisher frame/identity, actual broken-pipe retention without retry, and
the app's record_focus callback joining the memory event to an actual pipe frame.
The latter calls the callback helper directly; it does not synthesize Tk events
or create a GUI. All arms in the new app require MEMORY_ONLY instrumentation.
The original common FocusTrace component remains unchanged.

A second preparation-only Linux run used the same cached image/options with name
`ai-5260-a09-pipe-unit-20261004-02`. Exit 0; 53 tests in 0.105 seconds, all passed.
The same swap-limit warning was emitted. No GUI input occurred. App finish now
closes its writer before serializing the retained publication and close receipts.
Actual Tk lifecycle, candidate binding, gate injection and independent audit are
still unverified. No preparation test executes the candidate.run GUI workflow.

## Runner draft connection

Schedule and missing wrong-target click geometry tests failed before the A09
derivation. The existing refused-gate input test also passed, demonstrating no
key/Save callbacks when the gate is refused. The new schedule has ten apps:
NOW_TARGET four, PIPE_ACK_TARGET four, PIPE_ACK_WRONG_TARGET two; instrumentation
is MEMORY_ONLY in every row. The fixture now records 500ms timeout, 1ms poll,
50ms maximum age. A wrong-target arm clicks the decoy, not the target.

Runner code now creates a pipe per app, checks Linux PC_PIPE_BUF, inherits only
the writer, closes the parent writer, binds gate receipts to the actual child
PID/token/target/freeze hash, drains after child completion and retains raw read
and close records. Cleanup errors use setdefault so they cannot replace an
earlier runner error. This full runner lifecycle has NOT been exercised yet.

Third preparation-only Linux unit command used the same image/options and name
`ai-5260-a09-pipe-unit-20261004-03`: exit 0; 56 tests in 0.089s, all passed, with
the same swap-limit warning. No GUI input. These tests do not qualify the full
scientific allocation. Independent audit/source freeze/prospective allocation
recording remain necessary before the first candidate command.

## Independent pipe audit draft

pipe_audit.py imports only hashlib/json, not producer/decoder/gate modules.
Eleven mutated literal packets failed against its initial no-op implementation;
the implemented audit rejects those byte/identity/event/EOF/close/write failures.
It permits receive completion before the write syscall returns, rather than
imposing an invalid cross-process ordering.

Preparation container 04 passed 59 tests in 0.134s, exit 0. Its first live audit
test used an in-process duplicated writer and normalized fd metadata; this was
too indirect as lifecycle evidence. It was replaced with an actual subprocess
writer, inherited original fd, original unmodified close/read receipts and
separate JSON stdout. Container 05 ran that replacement and the full 59-test
suite successfully (see command output for actual duration), exit 0. Both used
the same image/options and emitted the original swap-limit warning. Neither
used GUI input. These are preparation runs, not a scientific allocation retry.
Full gate/sample/app/effect/source/file/role audit is still incomplete.

## Independent gate/sample audit draft

gate_audit.py independently reconstructs the latest received state at each poll
from original read-attempt count and received-frame timestamps. It checks source,
type, current target state, click/event/publication/decision order, receipt age,
deadline, refusal reason and zero refused input. Ten changed gate packets and a
refused-with-input packet failed against its initial no-op implementation.
The first implemented suite still failed its bool sequence corruption because
Python equality treats True as 1. Explicit integer checks fixed that test without
changing the input gate or weakening the expected refusal. Container 06 passed
62 tests in 0.159s, exit 0.

Two additional pipe-audit bool corruption cases were then added. The retained
frame bool sequence passed incorrectly and produced an assertion failure; strict
decoded-frame/publication checks alone did not fix it. Container 07 failed that
one assertion (62 tests, 0.159s, exit 1). Explicit retained-frame type checks were
then added; container 08 subsequently passed the full suite. These preparation-only
commands used the same cached image, read-only source and network-none options,
with the unchanged swap-limit warning. No GUI input or scientific allocation.
Remaining work: full source/file/environment/readiness/input/effect/load audit,
literal full packet tests, source freeze and prospective GitHub recording.

## Input/effect and load-window audit draft

effect_audit.py adds independent refused-input/effect checks and worker coverage.
Five refusal/geometry mutations plus two worker mutations were observed failing
against the initial no-op implementation; implementation passes them. A literal
admitted hxy packet also checks actual event-to-field/save consistency and rejects
a changed saved value. Refused apps must have zero keys/Save/events/field content,
and a busy worker must cover click through decision (or first key sync when
admitted), not merely exist. Its stdout start/end must match the retained receipt.

The unchanged A08 audit.py was copied as common_a08_audit.py for selected existing
read-only focus_trace/frame helpers; its old inspect/schedule/input/worker entry
points are not the A09 experiment auditor and must not be invoked as such.
PrivateCache/cache_audit retain the original A08 helper prefix deliberately;
every instance still owns a fresh path and A09 row token. No prior allocation is
reused. A top-level A09 inspector and complete synthetic packet test are pending.

Preparation-only Linux container 09: 67 tests in 0.249s, exit 0; same cached
image/options/warning. No GUI input. The first lookup of test_audit.py failed
because that filename does not exist in A08; rg located test_raw_audit.py and it
was inspected read-only. This lookup failure is not a scientific outcome.

## Complete A09 inspector preparation

audit.py now joins the independent source/image/environment/schedule/file/PID/
readiness/focus/pipe/gate/input/effect/cache/load gates for ten rows. Its finite
hypothesis requires four target-ACK rows admitted with exact hxy/empty decoy/no
post-receipt prekey target FocusOut, and two wrong-target rows refused with zero
input. Valid misrouting is H_FAIL, not an audit failure. NOW is descriptive.

The unchanged A08 synthetic packet builder was copied as synthetic_a08_packet.py
and wrapped by test_packet_audit.py to create ten A09 test-only pipe/gate records,
including two no-input wrong-target records. It is not a producer or experiment
result. Full packet initially failed the not-implemented entry point. It now
passes; three source/environment/count corruptions and seven file/app/cache
corruptions are refused. A target-ACK packet changed consistently to decoy h /
saved xy remains METHOD_PASS but H_FAIL. No real GUI input was used.

Preparation container 10: 71 tests in 0.533s, exit 0, unchanged swap-limit warning.
Fresh GitHub MCP CURRENT_GOAL and #5085 intake retrieved after this run; latest
CPU entries are A08 prospective/completed release, no new pending owner shown.
Local fetch advanced origin/main from 51a30a96 to 42387b40; own source branch
remains clean and has not yet incorporated that main update. Next before freeze:
inspect main delta/peer PRs, update own branch safely, verify prospective source
coverage and execution receipt commands, then commit/read back immutable source.
The A09 GUI candidate/auditor allocation has still not been executed.
