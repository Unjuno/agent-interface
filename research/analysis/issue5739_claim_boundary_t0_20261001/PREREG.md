# Issue #5739 T0 — survivor-family and false-elimination claim boundary

## H / T / D / C / U

**H.** In the frozen finite world, a claim-aware screening protocol will (1) refuse an unadjusted superiority/promotion claim for two survivors sharing one sealed cohort when no familywise inferential rule is justified, (2) withhold global-best claims when the screen excluded an arm that is actually best on sealed oracle outcomes, and (3) refuse promotion of a fastest survivor with a hard safety failure. An independent raw-only audit will reconstruct all attempts and reject each declared corruption.

**T.** Run one deterministic host-CPU candidate on `screen.json` and `confirmatory.json`. The candidate must not read `sealed_oracle.json`; that file is auditor-only, used to establish the false-elimination negative control. Four arms are screened; B and C survive and share matched variants v1–v4 against baseline A; E is fastest but has a hard-safety violation; D is screened out but is best under the sealed oracle. Report only exact finite descriptive deltas for B/C, no familywise superiority, no global-best, and no promotion of E. Then run one separate standard-library raw-only audit on candidate bytes. Verify mutations for omitted/duplicate attempts, repeated sealed variant, changed family membership, and forged safety. No GUI, model, game, input, network, Docker, GPU or CUDA.

**D.** `PASS_CLAIM_BOUNDARY_SCOPED` only if the candidate emits no unadjusted familywise promotion, no global-best claim, and no safety-invalid promotion; exact attempt/cohort membership and per-case labels reconstruct from frozen inputs; D is independently verified as the sealed-world best despite exclusion; and all five mutation controls are rejected. Otherwise return an explicit FAIL/HOLD with reasons. Do not compute p-values, infer exchangeability, or claim calibrated uncertainty.

**C.** Analyst-authored finite outcomes, static deterministic screening, and a standard-library host Python simulator/auditor. The finite world does not establish estimator quality, actual resource savings, real candidate performance, calibrated error rates, or live application behavior. The unavailable shared Docker lane is not used; this Issue explicitly permits host-only T0 when no named slot is available.

**U.** Confirmation outputs are deterministic synthetic examples; no empirical claim about Agent Interface follows. Screening quality, genuine data leakage/blinding, statistical validity, user impact, and any live integration remain unresolved. Preserve predecessor #5722 / PR #5733 unchanged.

## Freeze and execution boundary

- Base `main` at final freeze: `8627fb4ad928479be363c3d7754146dfc8afb793` (tree `8f01aaed9e3e69f96c3cb6ec4e6b08bf7d536eb7`). Initial issue/ownership intake read main `24f6b7d5f9395105807f981d48db212e6692a6f4`; final source freeze was moved forward after main advanced and before any candidate invocation.
- Candidate inputs: `screen.json`, `confirmatory.json`; oracle-only negative control: `sealed_oracle.json`.
- Candidate and independent auditor are distinct standard-library processes; auditor does not import candidate.
- One candidate invocation; auditor only after candidate exit 0; no retries.
- Host CPython on this Windows machine; no external model/service or shared compute resource.
