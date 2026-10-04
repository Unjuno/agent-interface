# L01 actual model-guided Draw recovery: first overall FAIL/HOLD

Issue2122; intake main25700c9f68e9937fc1057a5da91d14c3971bb2b6. One invocation/no retry. This differs from closed421's lock exclusion test and D01's Undo eligibility: actual provider actions feed a guarded relative movement workflow and are independently scored against saved application state. No historical run is replayed/regraded.

## Observed outcomes

|case|model action|model saved A/B x|fresh-read reference A/B x|expected A/B x|
|---|---|---|---|---|
|stable_unlocked|COMMIT|1200/2000|1200/2000|1200/2000|
|stable_locked|COMMIT|1200/2000|1200/2000|1200/2000|
|conflict_locked|RECHECK|1900/2700|1700/2700 **incomplete**|1900/2700|
|unknown_locked|RECHECK|1900/2700|1900/2700|1900/2700|

All rectangles y1000/size500×500; each document new and disposable. External writer is a separate actual Python UNO process connected to the same owned document. It changes A1000→1700 and B2000→2700 after the initial read; writer return and controller snapshots establish the directed order. Unknown masks the current snapshot only from the model; actual scorer state remains retained. Task authorizes A+200 from latest position, so external A displacement is preserved as the base, not literally unchanged. B must remain exactly external2700.

Model completed four turns, no tool items, COMMIT/COMMIT/RECHECK/RECHECK. Model4/4 and reference3/4 saved task endpoints; all8 preserve B. One additional fresh blind stale negative writes1200 from old1000 after writer1700: external base overwritten, expected1900 absent. Its failure is deliberate, not scored as production safety.

Overall frozen audit exit1 **FAIL_OR_HOLD**, error `task:conflict_locked__fresh_read_reference`. That reference sees A1700 at after_writer/recheck/admission, then calls Position1900; immediate final observation and independently parsed saved FODG both remain1700. Producer APPLIED/input_mutations=1 labels a setter invocation, not achieved effect. Do not expose those labels as verified completion. Cause unresolved; no exception, producer/container/soffice parent exit0. Retain the scientific failed task rather than attributing it to harness without evidence. No source fix, rerun or audit regrade.

## Model cost and interpretation

Requested gpt-5.6-luna/low, four fresh ephemeral CLI contexts, existing auth accessed by CLI on host only. Actual input55125/output350/cache0/reasoning163 (subset output). Host intervals5.297/11.922/10.406/8.375s, total36.000s include process/framework/transport/model/output. No inference-only latency, billing price or model snapshot available. Reference uses zero model calls. Fixed order and model waiting versus immediate reference are unmatched; reference failure does not identify model advantage, need, natural rate or causal speed/value. The prompt explicitly explains COMMIT/RECHECK semantics and lock limitation; this is guided policy use on real states, not blind semantic discovery. A simpler deterministic fresh-read policy already determines the correct intended operation; its observed incomplete effect requires investigation before it can be treated as an equal-correctness reference.

## Authority and environment limits

Current guard compares full A/B shape snapshots before mutation. Model cannot provide coordinates or bypass guard. This is value-bound current read in finite directed schedules, not authenticated document revision or generation, ABA detection, atomic check-and-write, exclusion of future writers or production authority. No writer is scheduled after guard. Identity names and protection are fixture-authored, though writes are genuinely independent process actions. No Undo, GUI/XTEST, real user document, GPU or cross-platform test. Existing D01 rejects blind Undo for direct Position; no selective undo framework proposed.

Pinned output imagebab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d from D01 public Debian build; actualLO25.2.3.2. Source/plan/schema/driver/writer/auditor and host CLI digest frozen before run. Source readonly bind/networknone/user65534; actual cgroup cpu100000/100000 memory536870912/pidsmax; swap warning retained. Root filesystem readonly/whole-host enforcement not claimed. Parent exits do not independently prove full descendant reclamation. Internal provider retries/actual billed totals unknown.

## Integration decision

**HOLD_MATCHED_RECOVERY_VALUE_AND_REFERENCE_EFFECT.** Actual model guidance produced correct saved task effects here, but integrated comparison gate fails and model necessity is unproven. Do not adopt this fixture driver as runtime or conclude model wait repairs application state. Next meaningful question is the reference setter/effect mismatch under a separately frozen matched schedule, including post-set/read timing and source geometry; not repeated prompts, blind Undo or reclassification. Preserve421, CalcR01/R02/M01, D01 and L01 all unchanged.2122 and ROADMAP remain open.
