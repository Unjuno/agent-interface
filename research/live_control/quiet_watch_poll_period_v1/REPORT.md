# Fixed 5 ms cue: 10 ms versus 2 ms ROI polling

**Decision: `PROMOTE_2MS_SCOPED` under the preregistered finite gate.** This is a scoped sampling/cost result, not a production or general-GUI promotion.

Task `QUIET-WATCH-POLL-PERIOD-20260916-001`, Issue #225. Publication BASE `24ae743ed63b56484a828f7916c303ba093449c7`; preregistered HEAD `441949f009fb0985b1472914b682787eb906b8c5`. Exact source SHA-256 `d50233d9584876f119e78251728ccbf682a4b46b5485197ae60229970d9d520d`. Formal `measured.json` SHA-256 `7d8756168e1aff11cc1ee1a82cb8552876c409e3ec9c69460f0ed56cda0d3aea`.

## Frozen question

Change one primary mechanism only: nominal ROI polling period, **10 ms versus 2 ms**, while keeping the declared 32x32 ROI, colour predicate, nominal 5 ms target cue, XTEST Right-key input, 600 ms owner deadline, cancellation path, final-clear check, target offsets and repetitions fixed. The measured allocation contains 30 target cases (15/arm) plus 8 nuisance controls (4/arm), randomized once with seed `21620260916`. No measured case was retried, replaced or added.

Construction failures before freeze were setup-only and excluded: missing Xauthority, Python-Xlib `str` image bytes, then one four-case qualitative preflight after those fixes. The exact 38-case schedule and decision gate were committed and recorded in Issue #225 before formal execution.

## Formal first outcome

| Endpoint | 10 ms | 2 ms |
|---|---:|---:|
| Target detection | **9/15** | **15/15** |
| Nuisance false cancel | 0/4 | 0/4 |
| Target cue→app release median | 4.457 ms | 2.371 ms |
| Nuisance acquisition-count median | 61.5 | 299.0 |
| Nuisance cumulative acquisition-call wall median | 12.326 ms | 60.625 ms |
| Max observed end→next-start gap in nuisance controls | 14.018 ms | 6.606 ms |

The preregistered cost ratio is **4.9185×**, below the frozen `<=5×` gate. All 38/38 cases independently verify empty Right-key release, exactly one application press/release and a clear final ROI.

Detection by offset (detections out of 3):

| offset after app press | 150 ms | 152 ms | 154 ms | 156 ms | 158 ms |
|---:|---:|---:|---:|---:|---:|
| 10 ms polling | 2/3 | 0/3 | 1/3 | 3/3 | 3/3 |
| 2 ms polling | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |

All six 10 ms target misses are mechanically explained by sampling gaps: each complete measured cue draw interval lies after one ROI acquisition ended and before the next began. The independent audit recomputes every stored ROI payload digest and match count and finds no classification mismatch.

## Important confound

The requested cue width was 5 ms, but software scheduling/rendering changed actual draw-completion intervals. The 10 ms arm median/range was **5.504 ms [5.271, 7.282]**; the 2 ms arm was **5.528 ms [5.177, 9.544]**. The heavier 2 ms watcher can itself perturb scheduling, so 15/15 versus 9/15 does **not** identify the pure causal magnitude of polling period alone. The retained claim is narrower: under this exact live-X11 workload, the 2 ms configuration passed the frozen correctness/cost gate; the 10 ms misses were genuine unobserved intervals.

## H / T / D / C / U

**H:** denser polling increases observation opportunities for a short declared visual event without violating release safety, at bounded acquisition cost.

**T:** one frozen 38-case randomized serial block, exact source/schedule hashes, actual X11 input and XGetImage observations, no retries/extensions/model/game calls.

**D:** **`PROMOTE_2MS_SCOPED`**. Detection improved 9/15→15/15, safety/integrity gates passed, nuisance false cancels stayed 0, and the preregistered acquisition-wall cost ratio was 4.9185× <= 5×.

**C:** increased watcher load also changes scheduling and can lengthen the rendered cue; a cooperative producer latch remains a different mechanism with different information assumptions.

**U:** one synthetic colour/ROI fixture, one unpinned shared host, finite descriptive sample, software draw-completion clock. Cumulative XGetImage call wall time is not total CPU utilization. No arbitrary-GUI, gameplay, hard-real-time or population reliability claim follows.

## Audit and retention

`audit.py` was run against the full formal raw JSON in the measurement container before publication. It verified the frozen schedule/count, source hash, stored ROI SHA-256 values and pixel reclassification, derived detections, one press/release, verified physical empty state, final clear ROI, cost medians and the frozen decision; `audit_result.json` retains that audit outcome (`formal_pass=true`) and the formal raw SHA-256.

**Retention limitation:** the GitHub MCP available in this session has no local-file upload action. A manual Base64 blob transfer produced a Git blob hash mismatch, so that blob was deliberately not linked into the branch. Therefore the 1,045,532-byte `measured.json` itself is **not** retained in GitHub in this publication step. Its SHA-256 is retained as `7d8756168e1aff11cc1ee1a82cb8552876c409e3ec9c69460f0ed56cda0d3aea`.

To keep the frozen decision independently recomputable from GitHub, `retained_evidence.json` stores all 38 case-level fields needed for schedule identity, safety/integrity gates, target detection counts, nuisance acquisition-wall medians and the six 10 ms miss-gap checks. `audit_retained.py` recomputes those gates from retained evidence plus the committed preregistration/source; `retained_audit_result.json` reports `pass=true` and the same `PROMOTE_2MS_SCOPED` decision. Raw ROI-byte reclassification itself cannot be rerun from GitHub alone without the omitted full raw JSON.

## Next single question

Do **not** immediately lower the period further. First separate sensing cadence from observer-induced perturbation: hold the 2 ms sampling schedule but replace full ROI acquisition with a lower-cost observation path (or equivalently calibrate acquisition without changing semantics), and test whether cue-duration distortion falls while detection remains intact. That isolates backend observation cost before composing producer latches or planner logic.
