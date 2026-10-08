# Issue #3944 — observer IPC freshness v3 retained result

## Disposition

**HOLD_FROZEN_AUDITOR_CONTROL_GAP**. The 40-case scientific matrix completed without retry, and the frozen raw auditor reported the scientific count gates as `PASS_CAPTURE_AND_DELIVERY_SCOPED`, but one preregistered corruption control was ineffective. Formal acceptance therefore remains HOLD.

This preserves two earlier execution records unchanged: the original 2026-09-22 `STOP_PREFORMAL_PUBLICATION_BLOCKED` / Draft PR #3959, and fresh v2 `STOP_OUTER_EXECUTION_TIMEOUT_NO_CHECKPOINT`. Neither predecessor contributes a formal row to v3.

## H / T / D / C / U

**H.** At CPython's fixed 5 ms switch interval, a separate XGetImage observer process can preserve short target acquisition while a CPU-bound thread occupies the consumer interpreter; IPC/package/GIL receipt delay is a separate freshness boundary.

**T.** 40 fresh directed pulse cases, ten four-case blocks. Arms: INLINE_IDLE, INLINE_THREAD, PROCESS_IDLE, PROCESS_THREAD. Five-ms red target pulses, 2 ms non-catch-up acquisition cadence over 120 ms, offsets 50/52/54/56/58 ms repeated twice. CPU0 consumer/observer, CPU1 load thread, CPU2 private Xvfb, CPU3 fixture. PROCESS uses a real JSONL subprocess pipe. Every ROI byte payload is retained. v3 changes v2 execution only by batch checkpointing and fresh Xvfb per block; cases have fresh r3 identities.

**D.** Frozen PASS required PROCESS_THREAD capture >=9/10, >=3 more cases than INLINE_THREAD, and <=5 ms conservative receive-age target in >=9/10 PROCESS_THREAD cases, plus complete integrity and effective corruption controls. Scientific counts meet these thresholds, but frozen controls reject 10/11 instead of all 11; overall HOLD. No threshold/source tuning or scientific rerun.

**C.** Process isolation changes address-space and scheduler placement as well as GIL sharing. Fresh Xvfb per block is also an execution reset. IPC/X-server scheduling can dominate, so the result is not an isolated causal GIL estimate.

**U.** No model consumption, task usefulness, tokens, end-to-end useful-feedback latency, real application, release safety, human tempo, production or cross-platform claim.

## First outcome

All ten batches completed once with external exit 0 and private-Xvfb cleanup. 40/40 cases retained.

| arm | target captured cases | <=5 ms receive-age target cases |
|---|---:|---:|
| INLINE_IDLE | 10/10 | 10/10 |
| INLINE_THREAD | 5/10 | 0/10 |
| PROCESS_IDLE | 10/10 | 10/10 |
| PROCESS_THREAD | 10/10 | 10/10 |

Frozen raw-only audit: 10,241 checks, errors=[]; nested scorer `PASS_CAPTURE_AND_DELIVERY_SCOPED`.

Frozen control suite: 10/11 rejected. `boolean_block` changed block integer 0 to JSON false and the auditor accepted it because Python `False == 0`. This is an auditor-integrity failure, not favourable evidence to waive.

A separately labelled read-only posthoc auditor adds only `type(block) is int`. On the same saved RAW it reports the same scientific counts, errors=[], and rejects 11/11 controls. It is diagnostic only and does not replace the frozen acceptance gate.

## Hashes

- FREEZE.json SHA-256 `277b350ce696ea181eb4672e7f2d98f55f4b6f84f6797a7b8699c6d13f07a103`.
- RAW.json SHA-256 `9e77997924f0073553acb9becdf2ee2c7e0d85f1b6c95eeffadd8f94e4dd8f03`.
- frozen AUDIT.json `dfb955a947e14343287152537ab7fd9f0439022506b258f2152033c5580c063b`.
- frozen CONTROLS.json `bb1982320a2f9bf891970e2b8495a68ca17fc59fa28d3cf849ce86e6a6878d50`.
- FIRST_OUTCOME.json `e35ec9920914b787fa01c7e1cbce23580b0e1aaa1c2d4d1631b43865e9902d17`.
- posthoc audit `575232cac847cf1319ba156385892120e6af1e1aeb32fdbc036c072ac37fdc25`.
- posthoc controls `a420b97cc3abc93a11ca7ecc4029aa4a42326f1b091a737ee1d1e514f792a3d5`.

## Integration decision

Retain the observed separation between acquisition and consumer receipt as scoped research evidence. Do **not** promote process-isolated observation solely from this allocation because the formal evidence-control gate is HOLD and no same-model/task benefit was measured. If a later integration uses this mechanism, require a fresh current-path compatibility/utility decision rather than rerunning this consumed matrix just to make the auditor green.
