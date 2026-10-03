# Primary startup readiness boundary — #57 / PR #6919 v3

A captured input/output error during awaited fresh exchange-directory creation
could be followed by a successful `ready` line. Automated finding4172146186
identified this window. The original source-pinned mechanism witness confirms
it: healthy publishes ready/terminal, fault preserves the original error and
closes the original relay but still publishes ready. One failure check immediately
after `createPrimaryExchange` prevents that known-fault readiness publication.
Whole-owner listeners, pending accepted work and original cleanup stay in place.

Prospective #57 claim5966809901 fixes H/T/D/C/U before the new ordinary checks.
Controlled startup cells inject an input error only after the actual mkdir
completes and while its promise is still awaited. The builtin hook is confined
to a separate Node child and restored; healthy completion is its control.
This is a mechanism witness, not an actual OS startup-device error or atomic
readiness guarantee. [Node builtin binding API](https://nodejs.org/api/module.html#modulesyncbuiltinesmexports)
documents the test hook; the child also checks the actual named binding.

## Actual first outcomes and repair

- First construction07:34:07.609762–07:34:07.994568UTC, exit1: both inert
  fixtures exited1 and had no start/exit record; the test helper then failed
  ENOENT. Its nested fixture string is retained. JSON.stringify source passing
  fixes construction only; missing child stderr is not recovered retrospectively.
- Repaired construction on unchanged V2 product07:35:58.767984–07:35:59.087269,
  exit1, 1/2 PASS: healthy ready/terminal, fault **ready** after captured error.
  Both original fixtures/hosts exit0, requests0, fixture PIDs absent and owned
  listeners removed. This is the actual product counterexample.
- One-line product repair07:36:39.777173–07:36:40.105691, exit0,2/2:
  fault publishes no lines; healthy remains ready/terminal.
- All19 affected stdio methods07:38:45.263313–07:38:46.059358, exit0;
  fixed6902/current V3 isolated composition07:45:42.305436–07:45:43.162318,
  exit0,22/22. Full actual streams and prospective source/argv/runtime pins
  remain. These are ordinary Mac Node26.7.0 checks, not hosted CI or V2 peer
  Windows results made current. Original45/20/V1/V2 evidence stays historical.

## Actual public CLI OS descriptor construction

The first separately frozen attempt uses an empty regular file and a directory
as FD0. Both actual CLI calls exit0 with ready/terminal, zero requests, child/host
exit0 and all4 PIDs absent. The directory did not produce expected EISDIR on
this MacNode26, so its checker exit1 and FAIL_PREDECLARED_OS_DESCRIPTOR_ERROR_INDUCTION
are preserved. It is not relabeled an error-handler PASS or a product defect.

A different fresh one-cell construction opens a regular FD0 O_WRONLY. The frozen
producer asserts F_GETFL's access mode before launching actual public `--config`;
numeric flags were not separately retained. At07:40:33.489089–07:40:33.591341UTC,
actual CLI exit2 and full stderr `EBADF` are observed; ready occurred before
the read failure, terminal did not. Original fixture PID8928/parent8927 have
correct ancestry, request bytes0, fixture/host exit0 and both PIDs absent; guard
unhit. This is real OS FD read-error evidence, not a TTY/device failure or the
controlled startup window. The earlier healthy control was not replayed.

## Separate saved-data oracle and custody

Independent stdlib reader imports no producer/runtime/test/auditor. Actual
exit0/observed07:49:08.653421UTC joins all5 actual Node check outcomes/full streams,
8 controlled witness rows, three public FD rows, original first outcomes and
retained source versions.10 copied semantic-validator corruptions reject known-fault
ready, bool/float status/PID, different child, request bytes, lost original error,
unrelated ancestry, hidden EBADF and falsely promoted directory error. These are
reader-validator controls, not new native interventions or all hostile-parser
paths. Its separate first started_utc was not captured and is not invented.

All tools/runtime/fixture copies are inert `.mjs.txt`/`.py.txt`. Owned private
workspace prefixes only are projected; PUBLIC_DERIVATIVES records every original/
public size/hash and suffix change. Original private bytes remain retained, not
reconstructed by hashes. SHA256SUMS covers every other delivered file. The large
Git scratch index is retained privately with its identity; trees are reproducible
from the prepared source snapshot/merge records. No original formal/native/
producer/auditor allocation is replayed, no source/raw/threshold is rewritten,
and no actual backend/SDK/native/GUI/model/input/task action is performed.

V2 fixed head83e92bbd, proposal5965736533/votes5966076053+5966553578 and UNSENT A01
remain historical. This source change requires a new fixed content epoch/three
assigned genuine nonauthor seats/two matching fresh approvals and a genuine exact
then-current base/head/tree application check before one expected-old forward
main-only send. No old vote, durable lock, future-tree authority or main request
is supplied here. The separate UTF8 normalization finding5966765165 is not repaired
or folded into this observer/startup change. Physical task effect, generalized
release/recovery, hard I/O/byte/time caps, efficiency, model efficacy and full goal
remain open.

The first staged raw-inclusive whitespace check exited2 only for the two retained
failed TAP streams (indented blank lines) and one exact archived test source with
an existing CR character. All original bytes stay unchanged. The explicit scoped
check excludes only those3 raw copies; its result is separate from full raw-inclusive
cleanliness, and all executable source/documentation paths remain checked.
