# E03 first native gate STOP — hypothesis unexposed

Disposition: **STOP_NATIVE_GATE / STOP_SESSION_WRAPPER_IMPORT**. The three-cell
native cancel/release hypothesis was NOT tested: first original_fault session
child exited before game startup/ready/observation/held input/fault injection.
Candidate_fault and candidate_healthy were never started. No game-control,
physical release, efficiency or production-fix result is claimed.

## Allocation and first result

Freeze88cee81c4e996bdc41ea46f6ef1f2f52209654ed published/read back on GitHub
before prospective Issue59 comment5973475287 and native launch. Scientific
sourceanchor96d39ca3855351b2501aab1da919941011190ac3. Source archive1917 files,
SHA256d1ad6dcb8720b27766702361b4898d13259d2efe0b173e7d0fbc970fe3d988db.
9 execution inputs checked before/after run. Exact image560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b
in own VM6183-t0; shared physical host, no exclusivity/performance claim.

Native container e03-native-fault-formal-3cbf-20261004 UTC
2026-10-03T21:05:51.386113492Z–2026-10-03T21:05:51.945538166Z, exit1,
OOMKilled=false. RUNTIME sampled UID501, CPU100000/100000,
memory1073741824/swap0/pids128. ChildPID8/PPID7 captured alive initially;
childexit1, cleanup_faults[], reader/drainer retired. Native stdout is empty.
Exact stdout and RESULT original bind files equal independent Docker-cp export.

Actual session stderr:
`ModuleNotFoundError: No module named 'doom_typed_release_backend_v1'`.
The reader waiter reported session exited before expected event; it did not
mistake the zero-event history for a .35s parse-fault comparison.

Cause: session_entry.py uses runpy.run_path while invoked from /experiment.
Unlike direct execution of /source/research/doom/session_map01_v12.py, run_path
does not add that script's directory to sys.path. Native session adds
live_control and observation_gating, not doom itself. The module DOES exist
in the hash-frozen source archive. PYTHONPATH=/source resolves repository
packages but not that flat sibling import. This is our instrumentation setup
failure, not an unavailable fleet dependency or production v39 defect.

## Official saved-only audit first failure

Frozen auditor executed once in separate offline/read-only own container
e03-native-fault-auditor-3cbf-20261004, UTC
2026-10-03T21:07:34.121605405Z–2026-10-03T21:07:34.306314122Z, exit1/noOOM.
It requires imports.json, which the failed wrapper never wrote; actual
FileNotFoundError is retained in raw/audit-command.log. No AUDIT.json exists.
There is NO semantic audit PASS. The auditor cannot validate a pre-import STOP
under its frozen success/import-custody assumptions. Its failure is preserved;
audit.py, producer and execution pins are unchanged after consumption.

Counts: formal native invocation1; session child1; completed game sessions0;
input submissions0/cancel commands0/fault injections0/model calls0;
saved-only official auditor1; native/audit retries0. Allocation CONSUMED.

## Method coverage and limits

Original gate stub RED16 failures; original auditor stub rejects no controls,
RED8 subcase failures. First repaired auditor still accepted raw integer1
versus RESULT true; failed GREEN-all retained. Independent review identified
four important exposure/custody/stop gaps, then a second terminal-record type
alias. Repaired before native launch; final source READY,12 pure methods pass
on host and own offline container. These methods cover gate semantics and
extracted reader/wait behavior, NOT the complete instrumented session entry.
The earlier successful direct-script preparation does not qualify the later
runpy wrapper. This missing execution-path check is the concrete preparation
gap exposed here. Do not extrapolate source review/unit green to native setup.

First freeze diffcheck flagged one trailing blank EOF in generated preparation
doom.ini. Exact raw bytes and failed diffcheck output preserved. A scoped
binary attribute for this generated config enables delivery diff checking
without altering its historical bytes. This is not a semantic runtime repair.

## H/T/D/C/U and next gate

H unchanged: typed receiver fault could support native cancellation while
input is held; unexposed rather than false. T executed first frozen native
attempt with firstfailure stopping; D precise wrapper-import and official
saved-audit failures retained. C preserve all preparation and failed allocation,
no blind retry, no production/controller/peer-owner mutation. U a new explicitly
named successor allocation requires qualifying its actual instrumented entry
path before freeze, retaining E03 untouched, and a partial-startup-aware
saved-evidence auditor. Do not create a new Issue just for this harness repair.

This report is evidence delivery under existing #59, not completion of its
real-time-control goal or ROADMAP. Production E02 adoption/receiver reopening,
useful gameplay/survival, model-loop comparison, time/tokens/human tempo,
general input neutrality, desktop integration and release gates remain open.
