# Action-bound prediction versus required evidence A01

Issue #6619's 2026-10-03 evaluation addendum asks whether prediction/origin alone is enough to suppress observations when some expected self-produced outcomes remain required effect witnesses. This is a new synthetic method successor to the completed #6632 cohort. It does not rerun or combine #6632's raster cases.

**H:** A prediction-only suppressor will suppress at least one correctly predicted but task-required cue in the yoked cohort. A completeness-aware gate can preserve every required and hard-critical cue while suppressing optional predicted cues, provided the source-bound receipt and `PROVEN_COMPLETE` relevance contract are valid. The reference implementation is imported byte-for-byte from `sources/observation_relevance_completeness_1726_candidate.py`, rather than recreated in this package.

**T:** A one-shot deterministic 1x4 binary-raster cohort crosses `SELF/EXTERNAL × MATCH/MISMATCH × REQUIRED/IRRELEVANT` (8 rows), plus hard-critical and unknown-receipt/unknown-coverage controls. The scorer-only oracle is stored separately from candidate inputs. Self and external matched rows are deliberately identical at the candidate-visible input: this is the yoked-causation control. Compare full-frame delivery, prediction-only suppression, and the exact #1726 `COMPLETE_ONLY` function from the pinned current-main source. The independent auditor reads candidate raw plus separate oracle, recomputes decisions and metrics, and checks four adversarial mutations.

**D:** `PASS_METHOD_SCOPED` iff candidate/oracle separation holds; matched yoked pairs preserve `UNATTRIBUTED`; full-frame forwards every changed cue; prediction-only suppression demonstrably loses a required or critical cue; complete-relevance has zero required/critical misses, zero late required delivery, falls back on invalid receipt or incomplete coverage, and suppresses at least one optional matched cue; all four audit mutations are rejected. This validates a finite method discriminator only.

**C:** Full-frame or the existing #1726 completeness baseline may dominate. A finite raster cannot establish semantic relevance or that real action receipts predict application pixels.

**U:** No live input, image, GUI, model, container, game, effect, safety, natural-event prevalence, task benefit, or Issue #59 live gate is established. In this synthetic fixture the completeness contract and deadline are trusted test inputs; runtime production of those contracts is outside scope.

The one-shot plan and exact inputs are frozen in `FREEZE.json` before candidate invocation. Candidate and independent audit outputs are retained without reruns.
