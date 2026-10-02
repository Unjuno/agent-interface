# Issue #6503 T0b — no-participant vigilance material and scorer validation

This is a new, additive continuation of #6503 after the distinct T0 preformal
STOP at `research/analysis/quiet_supervision_vigilance_6503_t0_20261002/`.
That predecessor remains byte-for-byte unchanged. No participant, user,
recruitment, GUI, model, or real oversight observation is authorized or used.

## H / T / D / C / U

- **H:** A finite recorded-episode package can preserve every assigned
  opportunity, independently reconcile source/effect truth and visibility,
  expose only source-bound facts under four declared displays (A continuous
  quiet stream, B evidence-triggered review, C fixed review, D hard-stop-only
  control), keep mandatory machine stops invariant, and score scripted scorer
  controls without oracle leakage. This is a material/scorer hypothesis only;
  it is not the Issue's time-on-task human-behavior hypothesis.
- **T:** Freeze 36 synthetic, non-sensitive opportunities in early/middle/late
  position blocks; independently sealed truth; exact onset/expiry, visibility,
  source/effect state and required safe action; A/B/C/D display schedule; a
  full 36×4 opportunity denominator; and scripted response controls for hit,
  miss, false alarm, no-response, late response, invisible anomaly and prompted
  hard stop. Run the material builder once in a pinned, isolated OrbStack Docker
  container, then a separate raw-only auditor once if the builder exits zero.
- **D:** `PASS_METHOD_SCOPED` only if all 144 policy-opportunity rows are
  present; B and C each contain six checkpoints with the same factual field
  schema and no oracle-only fields; hard-stop state and alert are invariant in
  A/B/C and explicitly shown in D; invisible opportunities stay in the assigned
  denominator but out of observable hit/miss counts; scripted controls score
  exactly; and dropped-row, truth-leak, visibility-flip, checkpoint-count,
  hard-stop-suppression, or score-corruption controls are rejected. Any
  mismatch is `FAIL_METHOD_SCOPED`; missing exclusive container authority or a
  failed start gate is `HOLD/STOP` before invocation. Construction tests are
  not the T0 result.
- **C:** B may improve cue salience rather than relieve vigilance; C may sample
  transient events poorly; explicit status displays, autonomy envelopes or
  takeover packets may make continuous monitoring unnecessary. Response
  criterion can change independently of discriminability.
- **U:** Hand-authored synthetic material and scripted response traces cannot
  establish what a person sees, recognizes, delays, decides, or does over time.
  Equal checkpoint count and field schema do not prove equal cognitive work.
  No sensitivity estimate, prevalence estimate, statistical power, policy
  efficacy, machine-safety validation, runtime, product, or human-tempo claim.

## Frozen design boundary

The 36 rows are a finite test corpus, not a human session and not a prevalence
sample. Anomaly opportunities include visible wrong-target and ambiguous-effect
events, a true but uncaptured event, and a mandatory machine hard-stop event.
Benign visual change and verified success are explicit non-anomaly controls;
the remaining routine events preserve the rare-event shape. Blocks are stimulus
positions only, not elapsed human time or evidence of vigilance decrement.

Every policy receives the same immutable machine gate. A/B/C always expose a
mandatory hard-stop alert; D is the explicit hard-alert-only display control.
For B/C, “matched factual access” means identical source/evidence field schema
at each review, not identical events or times. B's predicates derive only from
the public recorded observations. C's fixed checkpoints are predetermined.
Neither may read the sealed oracle. B's event-triggered timing is itself a
salience cue, so a future comparison must describe B as a cueing policy, not
pure vigilance relief. Discretionary checkpoint count is matched at six per
arm; the mandatory hard-stop alert is a separate invariant overlay. Equal
cognitive cost is not claimed.

The scorer is exercised only with synthetic scripted vectors. Each policy row
remains in the denominator, including unviewed/no-response rows. A true event
with no captured evidence is separately `unobservable`; it is not silently
called a human miss, a hit, or safe. Prompted hard-stop responses are kept out
of the unprompted signal-detection count. Hit/miss, false alarm, no-response,
latency and safe-action correctness remain separate fields.

## Execution boundary

No shared OrbStack Engine, another Issue's VM, WSLc, network pull, GUI, model,
human, or user data is permitted. The formal one-shot candidate/audit pair
requires an explicitly assigned exclusive CPU/container window on a dedicated
OrbStack VM with its own Docker daemon, an already-cached digest-pinned image,
and a fresh start-gate reconciliation. Candidate once; auditor once only after
candidate exit 0; retries zero. This package is not yet frozen for candidate
execution. Do not invoke either executable until the coordination Issue #5085
records the exact assignment and the complete freeze receipt is committed.
