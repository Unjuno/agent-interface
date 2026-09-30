# Ordered host timeline: primary one-form integration

Decision: retain this **opt-in instrumentation**, without changing the default
relay or claiming a performance gain. Source `c49abd9c0`; public runtime archive
source `2998586f5497e12940fe89992a398a2098298887`.

The primary assistant used the real public guarded MCP server through the new
wrapper on a fresh WSL/Xvfb Chromium allocation, seed 991330. The scope was fixed
before interaction to task-1 only. The inherited six-task oracle remains false
with tasks 2 through 6 missing; it is preserved, not relabeled as six-task success.
Independent submission history contains exactly one correct `t991330-1` save.

The 28-event host stream records review of the entered value at sequence 18 and
Save request at sequence 19. Both bind the retained reply; review additionally
binds call/source/image identity. No filesystem timestamp comparison is needed.
There were six calls: observe, two mints, enter, Save, and close. The assistant
viewed the entered value and then explicitly recorded review before Save. All
completed input releases and final close were verified empty. Transport and
fixture runner exited 0; tracked GUI children terminated with codes 0/1/1.

Host send-to-reply intervals were approximately 1309, 43, 39, 355, 322 and 41 ms.
Callback-completion to caller-review declarations were approximately 14.02,
9.52 and 9.64 seconds. These intervals include host/tool orchestration and the
primary assistant's processing. Callback completion is not model-visible
feedback; review declaration is not automatic understanding or semantic success.
No matched baseline, human comparison, actual model tokens/cost or instrumentation
overhead isolation is present. The gaps identify measurement boundaries, not a
proven performance bottleneck or speedup.

`python3 -O verify.py` checks 94 raw file hashes, event sequence and same-clock
ordering, exact reply/review identities, review-before-Save ordering, independent
saved value, input release, close and incomplete full-fixture outcome. The raw
archive contains requests/replies/images, setup/scope, host events, review
receipts, oracle history, cleanup, source snapshots and both test runs.

13 Node tests passed: eight existing relay/review tests plus five new timeline
tests. Controls include logging failure before submission (no request emitted),
logging failure after submission (retained reply, no replay), blocked overlapping
actions during asynchronous presentation, renderer failure, argument snapshots
and invalid/foreign review. Logging failures permit transport cleanup but do not
promote partial timeline evidence to success.
After this live allocation, failure messages were clarified to explicitly warn
that incomplete host evidence does not prove no input and does not permit replay.
The final 13-test run also checks that message; final-tests.log retains its output.
The raw archive keeps the exact earlier live host source unchanged.
