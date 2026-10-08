# Error-carry compilation of bounded directional intents — T0

## H / T / D / C / U

**H.** In the frozen constant-displacement fixture, an exact-rational cumulative-error schedule may reduce worst-prefix approximation error versus fixed and independent nearest-action schedules, with identical horizon and legal action budget. Whether that benefit survives discontinuous, nonlinear, or unsafe real actuation is unknown.

**T.** Ten frozen cases, four policies, 40 policy rows. Dictionaries are explicit: 4-way unit cardinals plus release; 8-way adds stipulated unit-diagonal vectors (not derived from key semantics). Cases cover exact east, shallow slope, near-axis duty, explicit diagonal, zero, reversed axes, one-slot deadline, outside-4-way-convex-hull intent, calibration mismatch, and a nonlinear acceleration/collision holdout. Candidate once; independent exact-rational raw-only auditor once; retries 0.

**D.** `FAIL_UNSAFE_SCHEDULE`. Candidate wrote an `exact-east` schedule with 4 eastward slots under the frozen x≤3 safety box; A, B, and C each reached x=4 and each has one envelope violation. This fails the frozen requirement that schedules stay inside the envelope. The independent auditor matched all 40 serialized policy rows to its recomputation, then exited 1 at its envelope assertion before the per-case improvement tally and mutation controls. No method PASS.

**C.** Main anchor `6cd70ad4bfad74e11658057bf024918bffb24add`; Python 3.14.5; stdlib exact rational arithmetic. Shared Docker/OrbStack ownership is unresolved (#5085/#626); no container is launched and T0 has no allocation requirement. This host-only synthetic computation does not access model, game, GUI, OS input, GPU, or network.

**U.** Even a scoped PASS is only a result for the stipulated constant-displacement action dictionaries. It does not show calibrated real keys, safe intermediate paths under collision/acceleration, live input occupancy, task effect, safety, human tempo, or MAP01 progress. The nonlinear holdout is not used to tune or claim transfer.

## Execution record

`FREEZE.json` records the pre-candidate inputs and source hashes. Candidate command: `python3 -B research/doom/discrete_intent_error_carry_6081_t0_v1/candidate.py` — exit 0, one invocation, 10 cases / 40 policy rows, raw SHA-256 `aca95bbbc8cb63a0eb1ab694deeb05ae791caa671442f2f593b3c5745945e292`.

Auditor command: `python3 -B research/doom/discrete_intent_error_carry_6081_t0_v1/audit.py` — exit 1, one invocation, assertion at line 48 requiring all scheduled policy rows to have zero box violations. It matched all 40 rows first; the frozen `exact-east` raw schedule exposes the unsafe candidate behavior above. Candidate and auditor are not rerun. Exact command outcomes are in `RUN.json`; failure classification and first stop are retained in `AUDIT_FAILURE.md`. No live traces are pooled or regraded.
