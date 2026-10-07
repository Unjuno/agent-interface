# Strict UTF-8 admission for the existing primary stdio

Actual worker01a0ff2e-17a3-70a1-908e-0d6dd78c45e9, FINAL-v5.
Parent#57; prospective repair claim5966851368 read back before tests.
First immutable public-byte finding5966765027/proofe3584aec showed two malformed
byte inputs collapsing into the valid U+FFFD request and consuming an ID.
This ordinary repair is limited to raw-byte admission in servePrimaryLines.

A built-in fatal UTF-8 checker runs before readline's later data callback.
It validates byte chunks incrementally and flushes at EOF; decoder output is
discarded, so valid existing decoding/framing/JSON/exchange semantics stay.
Malformed bytes set the same first-failure/intake pause/line-close path before
execute or ID consumption. Already accepted work and existing rejected writes
are still observed once before original owner cleanup. Only owned validation
listeners retire. No new line parser/action queue/replay/host replacement,
schema/default/cancellation/backend or input authority is added.
An unaccepted valid prefix in the same corrupted raw chunk is refused too;
already decoded string callers retain existing text but upstream lost bytes
cannot be recovered/validated. No hard I/O deadline or line-size cap is added.
Node's documented fatal/stream behavior and event listener order motivate this
use; actual installed-version evidence remains distinct from source API support:
https://nodejs.org/download/release/v24.6.0/docs/api/util.html#class-utiltextdecoder
https://nodejs.org/download/release/v24.6.0/docs/api/events.html#asynchronous-vs-synchronous
Alternate Node/ICU builds and actual Node22 execution remain unverified.

Test first:15 fixed literal methods, original RED7pass/8fail/exit1;
same definitions after repair15pass/0fail/exit0. Five malformed forms, incomplete
EOF, valid ASCII/split Japanese/literal U+FFFD/already-decoded text, existing
JSON/BOM refusal, same-promise committed work, corrupted unaccepted chunk prefix
and owned-listener/foreign-observer custody. Full first sources/freezes/streams/
argv/UTC/actual exits retained, not repaired into a favorable first outcome.

Additional exact current12 stdio methods plus15 new methods pass27/27 with no
skips/cancellations on Windows11 build26200/Node24.6.0, pinned binary
3428a3d055501883385d78b19128550d3e8be39a89e7edba683a9b06830257c7.
Source/config/fixture/collector/reader/bytes/settings/environment froze at
2026-10-03T07:50:55.165944UTC before commands. Maintained27 actual execution
07:50:55.476214–55.773864UTC; three new public --config/owned OS stdin cases
07:50:55.774834–56.341182UTC. CLI codes0/2/2; original fixture requests1/0/1;
all host/fixture exits0, guards unhit, empty collector stderr, all six PIDs
observed absent. Valid split Japanese+emoji preserves original value. Malformed
first request never reaches exchange/relay. A held already accepted request
returns once despite the later malformed bytes, then the same transport closes.
Fixture entry precedes corrupt writer and explicit own reply release; exact
internal validation/reply timestamps are not measured. Unit promise control
separately establishes the pending obligation. This is an inert echo child,
not an actual MCP SDK/backend/native operation or GUI/task/physical release.

Own saved-data reader imports no producer/runtime. First07:51:11.516537–
11.869832UTC/exit0 reconciles firstRED/GREEN definitions/15 totals,27 complete
TAP methods, all source/config/input/hex/command/full stream/UTC/typed exit/PID-
PPID-nonce/count/ID/held original/reply joins. Eight effective copied-record
controls reject Boolean exits/PIDs, changed nonce, invented second request,
normalized count, changed original label, reversed UTC and lost returned state.
Consistency-control refusal is not exhaustive hostile-parser coverage.

Delivery is four files: primary_stdio,15-method regression, its one-module
addition to existing Node workflow command, and public contract documentation.
All other workflow bytes are preserved. Full hosted Node/native Python workflow
was not run or claimed green. Publication commit uses skip-ci before branch
creation; optional CI is not a substitute for any later mandatory condition.
Measured test base9c0692dabbfc7fc2fa5bd111b6de4baee578800d;
publication basee5270c7bfe50911225afc6c3b5273021331b2bb1 has zero drift in
the complete used host/workflow/helpers/build/attributes/governing-doc closure.
All intervening paths are retained, including executable historical analysis
files; they are not called globally inert. No actual apply record exists yet.

#6919 author0975 retains its separate whole-owner/startup repair;#6902/#6879
retain theirs. This repair neither includes nor certifies those pending heads;
future combined source/used conditions must be checked before adoption. Old6919
content votes do not approve this change. A separately fixed prospective three-
existing-nonauthor committee needs two explicit content approvals, then one
nonauthor actual-current-base/head/tree/apply linkage, all real required gates/
ownership/cancellation and one expected-old history-preserving main update.
Main/source installation/shared runtime/ref/application lock has not been used.
No original five-cell assay/peer producer/auditor/formal/live allocation replay,
new worker or shared GPU/WSLc/display/Engine/model/input resource/deadline reset.
No task success, physical release, general finite recovery, token/latency/cost/
efficiency/full-goal completion result follows. All original private evidence
retained; public prefix derivatives bind original/public hashes. Historical
source/scripts are inert .mjs.txt/.py.txt and raw hex preserves invalid bytes.
