# Issue #8668 T0 A01 — phase-control delay result

## Disposition

**`PASS_METHOD_SCOPED` for the frozen synthetic finite plant.** The candidate emitted all 481 schedules once. The separately implemented raw-only auditor reconstructed every row with `errors=[]`, matched the policy decisions, and rejected all five frozen corruptions. This supports the specific abstraction discriminator in Issue #8668; it does not establish a runtime defect or live computer-control capability.

## H / T / D / C / U

- **H:** A static `CANCELABLE` label produces false cancellation/duplicate-admission traces after the modeled frontier, while `UNCONTROLLABLE` loses safe pre-emission cancellation; phase refinement avoids both within the frozen plant.
- **T:** One no-input control and 480 combinations of request phase, bounded control/reply delays, boundary order, effect/release receipt order, stale receipt position, and retry request; candidate plus separate raw-only reconstruction and five mutation controls.
- **D:** The frozen schedule count, reconstructed rows, static-policy counterexamples, phase-policy zero false cancels/duplicates, all safe removals preserved, and all five mutations rejected were required for `PASS_METHOD_SCOPED`.
- **C:** Operation-bound terminal accounting and `UNKNOWN` may already suffice without phase-refined synthesis; a different plant may have a static cancellation frontier.
- **U:** The event phases, delays, acknowledgements, irreversible frontier, and effect schedule are authored. No OS/backend behavior or real task outcome was measured.

## Result against the frozen gates

| Measure | Count | Interpretation in the authored schedule set |
|---|---:|---|
| Enumerated schedules | 481 | 480 requested-operation combinations plus one no-input control |
| Static-cancelable false cancellation claims | 126 | A delivered cancel command was treated as cancellation although the effect could still commit |
| Static-cancelable unsafe duplicate admissions | 63 | A retry was admitted while the original operation was unresolved and later committed |
| Static-uncontrollable missed safe cancellations | 228 | The bounded schedule allowed operation-bound removal confirmation before emission |
| Phase-refined safe cancellations preserved | 228 | Every cancellation opportunity classified safe by the frozen plant was retained |
| Phase-refined retries blocked while `UNKNOWN` | 63 | Neutral-input receipt plus timeout did not authorize a retry before the effect receipt |
| Phase-refined false cancellations / unsafe duplicates | 0 / 0 | Matching pre-emission removal proof is required; otherwise retries remain gated |
| Mutation controls rejected | 5 / 5 | Phase relabel, delay-bound shift, dropped case, stale operation ID, release-as-abort |

The fail-closed baseline also admitted no retry; it missed the same 228 safe-cancellation opportunities in this model. The `UNKNOWN` blocks and counts are consequences of the authored transitions and receipt schedule, not measured rates.

## Reproduction and provenance

- Frozen main: `23d1807ffad8359e0f89421ee2b9bf5783c9d5f4`.
- Frozen source commit: `766297bbadd674bb76d5e83968a7aa5e12cb04eb` on `research/8668-phase-control-delays-a01-20261009`.
- Run ID: `PHASE-CONTROL-DELAY-8668-T0-A01-20261009`.
- Environment: Darwin arm64, CPython 3.14.5, standard library only.
- Candidate: `python3 -B candidate.py > run-01/candidate.json 2> run-01/candidate.stderr`; one invocation, exit 0.
- Auditor: `python3 -B auditor.py run-01/candidate.json > run-01/audit.json 2> run-01/auditor.stderr`; one invocation, exit 0.
- Candidate raw SHA-256: `9977d26c82ff6c30152b66290c7690856dfcab45e377334f31fd358da20d0678`.
- Audit SHA-256: `a9c11cabef70c3ea75dd585d8a2f3a39af36f81aeed662d06d996b3c33cc49ac`.
- `FREEZE.json` holds the pre-run source hashes and invocation bounds; `RUN_LOG.md` records the first outcome; `SHA256SUMS.txt` contains the artifact digest list.

## Limits and next decision

The model fixes `EMITTED` as the irreversible boundary, assumes a non-idempotent effect commits after emission unless removed beforehand, and authors the cancellation, release, timeout, and receipt rules. No OS/backend/runtime event was observed. The phase-refined result is a model-policy result; it does not prove that a GUI backend exposes the phases or acknowledgements, that any implementation follows this policy, or that a real task succeeds. No latency, model-call, resource, human-tempo, general safety, or product claim follows.

The scoped result justifies keeping phase-indexed controllability in the candidate abstraction for a later separately authorized backend transfer. It does not authorize a GUI/runtime allocation. No formal live allocation was consumed or retried.
