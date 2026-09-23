# Guard-policy recoverable X11 calibration R2 — retained formal stop

Issue #1722. Direct predecessors #1646 and #1672.

## Disposition

**STOP_FORMAL_SUCCESS_OBSERVATION_DEADLINE**

Formal invocation **1**. Reruns0 / replacements0 / tuning0. This Task ID is not rerun.

No `FORMAL_RESULT.json` was produced and neither formal auditor ran, so this is not a selector PASS or selector FAIL.

## What had passed before formal

Excluded construction established the intended recoverable route:

- stale cached LEFT click is an independently logged no-op;
- fresh fallback localizes RIGHT and reaches the common success terminal;
- exact LEFT ROI guard has observed construction sensitivity1 and false-reject0;
- baseline-subtracted construction estimates for `c_y_stale`, `c_y_fresh`, and `c_f` were nonnegative;
- four held-out q tiers exposed three resolved policy orderings with selector disagreement0;
- primary and independent construction audits passed.

The formal science source was then frozen and read back as seven exact Git blobs. The frozen scientific constants include a 3 ms stale-no-effect detection wait and a 20 ms success-status observation deadline.

## Formal first outcome

The single formal invocation progressed into the q=1/100 held-out policy block and stopped at:

`policy-1/100-0219-POST_ONLY`

with:

`RuntimeError: heldout fresh direct failed`

The controller did not observe the success-status pixel inside the frozen 20 ms success envelope.

However, the independent application log records that same fresh LEFT click as a valid task success:

`{"episode":"policy-1/100-0219-POST_ONLY","kind":"click","pos":"LEFT","result":"success","ts_ns":7090688242891,"x":80,"y":100}`

The episode reset was logged at `7090637116067`, 51.126824 ms earlier. That interval includes setup and is **not** claimed as click-send-to-effect latency because the incomplete row never committed the controller click-send timestamp.

Thus the retained evidence supports only the execution diagnosis: a successful task effect existed app-side after the controller's 20 ms success-observation envelope failed.

## Why this is not a scientific FAIL

The experiment had not emitted its formal result object, policy-tier summaries, or audit inputs. The stopped row is fresh, not stale, and its cached click was correct according to the independent app log. There is no evidence here that #1646's selector ordering was wrong.

Likewise, the 3 ms stale no-effect wait is not implicated by this row. The two envelopes serve different semantics:

- 3 ms: decide that an old inert click produced no effect before fallback;
- 20 ms: observe a known-success effect after a correct click.

A successor may change only the latter.

## Integrity

Post-stop source SHA-256 remains byte-identical to freeze for all six science files.

Evidence commitments:
- partial fixture log: 260,905 bytes, SHA-256 `a360bb04febce9003ebd9ebc2f9988035a2eb411e7ebcd486841fc625c838459`;
- stderr: 779 bytes, SHA-256 `c61ef1edcb080827258d63bbc418e06aa1bf4bac080a6983211d4ec50e2f9b7a`;
- stdout: 53 bytes, SHA-256 `8e3db63f0502051fc0c47c3fd8806f439b58c95f9002db4764448543a6648241`;
- deterministic stop tar.gz: 23,591 bytes, SHA-256 `fc62f8186eb6db18c2e110a999666d105e239361feac2c78b29761fac8177d65`.

The full partial app log and lossless stop bundle are hash-committed but not copied in full into GitHub. Exact formal source remains reconstructible from the retained seven source chunks. No result was regenerated and no case was rerun.

## Next legal successor

Fresh Task/Issue only. Change exactly one operational factor: increase the success-status observation envelope from 20 ms to a preregistered fixed value. Keep unchanged:

- recoverable no-op route and fixture;
- 3 ms stale no-effect wait;
- guard ROI/classifier;
- calibration equations and baseline subtraction;
- q={1/100,1/20,1/5,1/2};
- calibration/formal corpus sizes;
- bootstrap procedure;
- selector and decision gates.

Before the successor formal allocation, a separate construction/preflight must demonstrate that the new success envelope contains fresh successful effects without changing task semantics.
