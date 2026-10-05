## Evaluation addendum (unverified): separate causal origin, prediction match and task relevance

**Transfer / paradigm-challenge refinement within #6619, not a new residual algorithm or an executed experiment.** Generic reafference/motion compensation is already proposed here and #6632 retains its method evidence. The remaining evaluation question is whether an “external event” endpoint alone adequately covers **important, correctly predicted consequences of the agent's own action**.

### Primary source and transfer boundary
Schneider, Sundararajan & Mooney, *A cortical filter that learns to suppress the acoustic consequences of movement*, Nature 561, 391–395 (2018), DOI https://doi.org/10.1038/s41586-018-0520-5 ; authors' institutional abstract https://scholars.duke.edu/publication/1353886 .

The abstract describes acoustic virtual reality in mice: experience linking movement with a novel tone selectively attenuated cortical responses at that tone's frequency, with improved detection of non-reafferent tones during movement. Read scope is the full institutional abstract, not the underlying methods, neural data or supplemental controls; journal/PMC full text was inaccessible in this lookup. This supports learned action–sensory prediction in that animal task, not a GUI safety rule, proof of causal actor attribution, or the claim that expected/self-produced observations are unimportant.

### Specific problem / structural analogy
A task can require the agent to observe a *self-produced* expected result: an exact Save acknowledgment, validation message, changed selection, a drag landing on the wrong target, or an anticipated modal requiring a new decision. Some of these are important even when they are neither exogenous nor surprising. Conversely, an external animation can be task-irrelevant. Predictor accuracy and causal origin cannot alone decide whether to omit evidence.

The biological filter's movement-correlated sensory prediction maps to an input-bound visual predictor. The useful difference is that an Agent Interface observation is also a **task/effect witness**; a correctly anticipated visual change may still be necessary for verification, branching, revocation or recovery. Suppression of neural response in a mouse is not equivalent to dropping a source frame from an agent's decision/evidence path.

Separate three axes in a future event ledger:
- **Origin:** independently attested SELF / EXTERNAL / UNATTRIBUTED.
- **Prediction relation:** MATCHES_FROZEN_ENVELOPE / MISMATCH / UNDEFINED.
- **Task relevance:** REQUIRED_EFFECT_OR_BRANCH / HARD_CRITICAL / IRRELEVANT / UNKNOWN.

Origin/prediction metadata never supplies completeness, effect success or action authority. Distinguish stored raw retention, scorer access, local mandatory-watcher access and evidence actually delivered by the required decision deadline. A frame retained on disk but withheld until after the decision is not timely task evidence.

### Proposed minimum discriminator
Expand only a separately frozen future cohort, not the consumed #6632 package:

1. Cross SELF/EXTERNAL × prediction MATCH/MISMATCH × REQUIRED/IRRELEVANT in a small independently authored raster/task table; keep separate HARD_CRITICAL and UNKNOWN controls. Freeze the predictor and relevance contract before scoring.
2. Include **expected self-produced required evidence**: the admitted action causes the exact predicted change, yet the current task requires confirming that change before the next branch. Include a benign expected self-motion case and an externally caused but predictable required cue.
3. Add a **yoked receipt/control**: same raster sequence and timing, but a fixture's independent action-delivery/event log differs. This tests whether an arm labels causation from temporal prediction alone. Where allowed observations cannot distinguish origin, require UNATTRIBUTED rather than treating an oracle label as candidate input.
4. Compare existing raw delta, action-agnostic registration and action-bound residual with the full-frame/required-evidence baseline and the already specified complete-relevance gate. Keep equal capture/delivery/alarm budgets where meaningful; separately report extra mandatory delivery cost. Independent labels are scorer-only unless a declared runtime contract truly supplies them.
5. Score timely *required-evidence delivery*, critical misses, origin-label errors, false optional alerts, effect/branch correctness and UNKNOWN fallback. Report exogenous-event detection separately; do not turn a self-produced required cue into a non-event false alarm simply because it was predicted.
6. Never train or fit an adaptive cancellation model on the held-out important events. This comment proposes no learning rule and does not assume the existing predictor is adaptive.

**Analytical witness, not a run:** identical source/current frames, input receipt and predicted transform can be paired with two task contracts: in one, the changed region is irrelevant; in the other, it is the required effect witness. A gate seeing only prediction match/origin gets the same input while the required delivery differs. Thus those fields cannot universally establish suppressibility. This is the relevance-completeness problem already owned by #1726, not a new impossibility theorem or an additional suppression certificate.

### Novelty / overlap and retained outcomes
Refreshed main README/CURRENT_GOAL/ROADMAP; inspected #6619 and all comments, merged PR #6632, #47, #1726 with result comments, #5671 and #5764. All-state Issue searches covered efference, reafference, self-generated/self-caused critical, expected-change/relevance, predictable safety and action-yoked controls. Closed prediction/relevance search and PR/branch checks found no separate same crossed cohort. Bounded search cannot exclude unpublished work.

- #6619's original critical-predicate/full-frame fallback is already necessary and remains unchanged. This addendum makes **task-required but non-hard-critical predicted evidence** explicit in the endpoint denominator; do not claim the original algorithm has been shown to lose it.
- #47 already requires conservative mutation actor attribution: a change after an action is not proof of self-causation. Yoked controls test that contract; residual matching does not replace it.
- Closed #1726 reports 49,152 finite rows, 6,144 false suppressions from assumed completeness versus zero under its truthful complete gate, plus 7/7 rejected controls, merged via #1733. It already subsumes the generic completeness requirement. Use its gate as the strong baseline; no new mechanism is justified if it already handles every proposed cue.
- #5764 separates novelty from effect relevance for *post-event audit triage*; this addendum tests timely observation delivery during self-motion, not another audit queue.
- #5671's weak-shift sentinel cannot repair a correctly predicted relevant event by waiting for surprise. Its historical shift-risk predecessors remain unchanged.
- #6630 retains STOP_AUDIT_MUTATION_CONTROL_DEFECT. #6632's one WSLc candidate and raw-only audit reconstructed 16 pairs/five events; raw delta and action-bound residual both detected 5/5, with matched valid-pan false alerts 2/2 versus 0/2. This is method evidence, not efficacy or live safety. No origin×prediction×task-relevance conclusion is inferred from those counts; no old label, source, denominator or outcome is changed.

### H / T / D / C / U
**H:** A predictor/origin-only suppression rule can miss task-required evidence even with a correct action prediction; the existing task-completeness/mandatory-evidence gate should reject that false promotion. A more specific residual policy has incremental value only if it reduces optional alert/delivery work against that strongest baseline while preserving timely required evidence at the matched budget.

**T:** Minimum future method study is the frozen crossed table and yoked/UNKNOWN controls above, using an independently specified task/effect oracle and raw-only reconstruction. Only if actual source-bound visual traces and a separately authorized disposable fixture exist should a real held-out comparison follow. No induced consequential action, model call or live game allocation is granted here.

**D:** PASS_METHOD_SCOPED requires all required/critical evidence delivered by its declared deadline, all origin ambiguities preserved, every label-leakage/late-delivery/missing-required-cue mutation rejected, and no zero-residual ⇒ safe/effect-complete inference. FAIL_METHOD for loss of a correctly predicted required cue or causation fabricated from matching pixels. H_FAIL_INCREMENTAL if full-frame or complete-relevance baseline matches/dominates residuals at equal resources. HOLD_NO_RELEVANCE_ORACLE / HOLD_ORIGIN_UNIDENTIFIABLE where needed, rather than declaring suppression safe. A finite PASS is not a learned predictor, real-time game or product safety result.

**C:** The existing #1726 relevance contract and #6619 hard/full-frame lanes may already solve the entire residual. If so, this is a benchmark-coverage refinement only, and no new filter should be built. Apparent missed evidence could instead be capture cadence or presentation delay.

**U / value / cost:** Relevance depends on current intent and effect/branch obligations; a finite suite cannot prove complete semantic coverage. Actual input receipt need not imply delivered effect. Yoked histories may be observationally identical, preventing origin identification. T0 is low-cost CPU/raster work suitable for eligible WSLc, but requires a new owner/freeze rather than replaying #6632. The expected value for O2/O3/#59 is preventing biologically motivated “expected means ignorable” logic and ensuring the event denominator includes relevant endogenous outcomes.

No implementation, experiment, container/model/GUI invocation, branch mutation, learning fit, or consumed-allocation rerun occurred for this addendum.

