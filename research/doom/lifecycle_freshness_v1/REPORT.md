# Lifecycle freshness v1 — real MAP01 notification-fault experiment

Decision: **PROMOTE scoped stale-lifecycle admission refusal; do not promote to shared runtime.**

Issue #187. Publication base `1308b57d3209bc32b3bea5b84efb4911c915d8e9`; immutable executed runtime `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. Source/threshold freeze head `9f6b13f60ca8950aff9b239fc9f984d340c0d7d5`. Exact new research paths only; zero model calls.

## Question

The preceding lifecycle experiment showed that a trusted terminal receipt can cancel held input promptly. This successor asks what happens if that receipt is **lost or delayed**. The candidate deliberately does less than a timeout-to-terminal heuristic:

- silence never means terminal;
- stale lifecycle evidence never cancels already-active input;
- the existing owner deadline remains the active-input backstop;
- a **new submit** requires a recent trusted same-epoch lifecycle receipt;
- a real terminal receipt still latches the epoch and cancels the matching active intent.

Freshness is fixed at **300 ms**, three nominal 10 Hz evaluator periods. This is provider-specific calibration, not a universal constant.

## Retention and harness failure

The original frozen allocation had 12 first-outcome IDs. Eleven completed. `r2-delay_fresh` reached terminal cancellation with independently verified empty input, but the outer multi-case tool hit its 240-second limit before late-submit/finalization. That ID was **not rerun** and the original allocation remains formal FAIL/INCOMPLETE. Its primary phase is retained separately: engine-end observation to empty 570.266 ms; delivered terminal to empty 1.567 ms.

A separately frozen, same-source, same-threshold repair replication `repair-r4-delay_fresh` was then run once under new identity. It supplements the mechanism evidence but does not relabel the original 12-case allocation as complete.

## Actual complete results

| Condition | Complete n | Primary | Late submit | Key timing |
|---|---:|---|---|---|
| terminal dropped, no freshness gate | 3 | expired 3/3 | **admitted 3/3** | end-observed→empty median 2381.502 ms |
| terminal dropped, 300 ms freshness | 3 | expired 3/3 | **rejected stale 3/3** | end-observed→empty median 2375.024 ms |
| terminal delayed 500 ms, freshness | 3 | cancelled 3/3 | rejected ended 3/3 | end-observed→empty median 576.182 ms; delivery→empty median 1.168 ms |
| still running, freshness | 3 | expired 3/3 | **admitted 3/3** | late-submit evidence age median 26.004 ms |

For dropped-terminal cases, last trusted running evidence was about 2.6 s old at late submit. With freshness disabled the late action was accepted 3/3; with the 300 ms gate it was rejected 3/3. Crucially, the primary input in both arms still expired at the unchanged owner deadline: the stale gate did **not** infer termination or accelerate active release. Median end-observed→empty differs by only 6.478 ms descriptively, with no efficacy interpretation.

When the terminal receipt was delayed, the active input continued until that real receipt arrived. Complete cases released 0.842–1.303 ms after delivery. The mechanism therefore propagates notification delay rather than pretending silence is task end.

Still-running controls retained fresh evidence (late-submit age 25.983–30.114 ms) and admitted the late action 3/3. The gate did not become a blanket stop switch.

## Integrity and separate scorer defect

All 12 complete mechanism cases (11 original + one repair) pass the per-case source, acquisition, action, release, and controller-delivery audit. Scorer missed periods total **0**. Every primary release is independently verified empty. Timeout cases still preserve the historical `score.json` false map-exit mismatch; this experiment does not fix or hide that separate classifier defect.

The dropped-terminal fault injection affects lifecycle delivery to the admission/revocation gate only. The evaluator continues recording actual terminal engine state off-policy. Thus the experiment tests a notification channel failure without deleting ground truth from the retained evidence.

## Environment

| Condition | Value |
|---|---|
| Engine | ViZDoom 1.3.0 / Freedoom MAP01 / ASYNC_SPECTATOR 35 tics/s |
| Fixture | retained `map01-threat-contact-v2` save SHA-256 `cc5302aa...` |
| Input | real XTEST through unchanged Executor/InputOwner; `[a,d]` chord |
| Requested / owner authority | 5000 ms requested / 3075 ms owner deadline |
| Evaluator | 10 Hz one-tic refresh; scorer never enters policy |
| Display | private Xvfb/Openbox; visible 640x480 game |
| Host | same disposable container host as predecessor; clock unpinned/shared load |
| Batch | one session at a time; three restores per principal condition |

## H / T / D / C / U

**H:** stale same-epoch lifecycle evidence can safely refuse *new* authority after a terminal notice is lost, while the existing owner deadline bounds active input and fresh running receipts preserve availability.

**T:** 13 deterministic unit tests, one excluded real preflight, then the frozen 12-case matrix. One harness timeout is retained; a separately frozen one-case repair replication completes the missing delayed-notice late/final path.

**D:** scoped PASS for the mechanism: dropped-terminal freshness rejects late submit 3/3, matched no-freshness accepts 3/3, running freshness accepts 3/3, delayed real terminal cancels complete cases only after delivery. Original 12-ID allocation itself remains incomplete due the retained harness failure.

**C:** a provider that continues emitting fresh but falsely `running` receipts defeats this freshness mechanism. A shorter threshold can create availability failures under host stalls; a longer threshold enlarges the reauthorization window.

**U:** one provider, one saved state, small n, synthetic notification fault injection, no model/planner, no map exit. The 300 ms value is not portable without a provider cadence/latency contract. No hard-real-time, arbitrary-GUI, gameplay, or security-authentication claim.

## Next discriminator

Test **fresh but semantically wrong lifecycle receipts** separately. Freshness alone cannot detect them. The next general mechanism should bind lifecycle assertions to a provider generation/transition proof or independent corroboration rather than making the freshness window increasingly conservative.
