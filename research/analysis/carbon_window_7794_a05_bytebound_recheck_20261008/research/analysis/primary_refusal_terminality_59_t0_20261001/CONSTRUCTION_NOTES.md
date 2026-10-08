# Construction notes

Before the one-shot candidate run, the initial `node test.mjs` process exited
with a TypeError from the frozen subject's `read()` when the mock returned an
empty response object. The test harness had not caught the caller exception as
an external primary would. This was a harness-modeling defect; candidate
invocations remained 0. The harness was corrected to catch that exception and
then attempt the next guarded call, which is the safety-relevant boundary under
test. The frozen subject source was not changed.
