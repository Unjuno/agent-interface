# V39 owner release-query failure boundary probe A01

## H / T / D / C / U

**H:** In current PR #7805's V13 `InputOwner`, a successfully sampled per-key physical-up row can be lost when the later aggregate `query_pointer()` or `query_keymap()` raises before `owner_release` is appended. The bridge can only drain recorded owner records, so the evidence row and bridge reconciliation may both be absent.

**T:** On current main `16c74566b64f32d7fe035c7724bcfe3865863a91`, load the exact V13 owner and V2 bridge source blobs from PR #7805 head `1ef5611356ff217f0981843ae854ef871967e999`. Use the retained V39 fake-display harness for three same-path cases: successful cleanup control, one injected aggregate pointer-query failure after key-up, and one injected aggregate keymap-query failure after key-up. Each case admits F8, sets the cancel event, and observes owner records, emitted bridge rows, fake physical state, owner state, and bridge `held`. The runner saves its raw JSON before evaluating the frozen decision.

**D:** `PASS_REPRODUCED_RECORD_LOSS` requires the control to emit exactly one confirmed-up row with empty owner/bridge/physical state, while both injected failures occur after fake physical key-up and leave zero owner-release records/zero emitted release rows, with F8 still in owner and bridge ledgers. Any deviation is `FAIL_HYPOTHESIS_NOT_REPRODUCED` or `STOP_HARNESS`.

**C:** This is a deterministic fake-display owner/bridge boundary probe. It isolates exception ordering and does not establish real X server failures, live frequency, application consumption, useful feedback, recovery, game behavior, or physical keyboard state.

**U:** One owner/bridge source pair, one fake-display implementation, and one invocation with three deterministic cases. No candidate run, real display, GUI, game, model, OS input, container, or live allocation is involved.

## Reproduction

Run once from the repository root:

```powershell
python research/doom/map01_v39_release_query_failure_probe_a01_20261005/run_probe.py
python research/doom/map01_v39_release_query_failure_probe_a01_20261005/audit_probe.py
```

The input source snapshots are exact bytes from PR #7805. The harness and its current-main dependencies remain repository paths pinned by `FREEZE.json`. `results/construction-a01/outcome.json` retains the raw case observations. The independent auditor reads those bytes and the raw JSON; it does not import or rerun the candidate.

The first wrapper invocation stopped at its source-hash precheck before loading the owner or executing any case; the original freeze and command output are retained under `results/preflight-stop-a01/`. The comparison bug was corrected before the sole probe invocation. This preflight STOP is not a candidate or probe outcome.
