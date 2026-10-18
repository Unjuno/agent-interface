# T0 result — Issue #8150

Allocation: RUNTIME-ELIGIBILITY-8150-T0-20261005-01  
Preregistration: commit 17ee2cb2f555344ad3207c73ea0c6366220ff80b; cases and evidence map subsequently frozen before review at commits 2269c8b91e554f3eff21ad207ca7bb1b478d25c6 and 8c2581b97008f25ba621ca933db4d11433008c16.  
Base main: aeed696ff756d68497faed39b92e3546cb144972.

## Disposition

**HOLD_REVIEW_DISAGREEMENT.** No runtime/container/network/process/memory/filesystem operation occurred. Two isolated reviewers each classified seven profiles across five runtime categories (35 ordinal labels per reviewer). Their weighted Cohen's kappa, with INELIGIBLE < HOLD < ELIGIBLE_SCOPED and linear weights 1 - |i-j|/2, is 0.8955223881 (35 cells; observed disagreement 0.0142857143; expected disagreement 0.1367346939), above the preregistered 0.70 threshold.

Both independently identify a material trust-boundary mismatch: a route-only checklist keyed to single-container CPU/no Compose can default to WSLc for arbitrary untrusted code, while the required Windows-user/peer isolation is not established by WSLc or ordinary process containers. The card must reject WSLc/native WSL for that profile and route to a separately managed VM only as a requirement, not as an availability claim. Both also distinguish a requested memory flag from an effective cap; #6355's 384 MiB counterexample remains decisive. Both classify network denial as HOLD because --network none is configuration-only in this evidence packet. The runtime default is not contradicted as a blanket rule: the result shows its eligibility qualifier needs a threat/asset check to be operational and auditable.

The blind reviews did not fully resolve the frozen mutations. M1 and M2 were handled consistently. For M3, reviewer A kept case 2 INELIGIBLE because the profile still names the protected assets, while reviewer B said HOLD when the threat-boundary premise is omitted. The preregistration required HOLD/UNKNOWN for this mutation and forbade author tie adjudication. The wording is materially ambiguous about whether the boundary premise is removed from the card's evidence map or the profile's requirement; do not change it post hoc. The frozen D gate therefore yields HOLD, not PASS.

One additional scope distinction emerged: historical capability evidence and current launch readiness are separate axes. The #7924/#7970 ownership gate means no present WSLc operation is authorized, regardless of a narrow historical portability/EROFS receipt. Reviewer B also marked native WSL eligible for the trusted CPU case only conditionally, while reviewer A retained HOLD for missing current health; this contributes to the single ordinal disagreement but does not affect the WSLc case-2 mismatch.

No effective security boundary, network block, hard memory enforcement, currently available VM, Docker availability, or WSLc current health is certified. This method-only review is not a security assessment/certification and authorizes no execution.

## Reproducible agreement calculation

For each reviewer, enumerate cases K1–K7 in order; within each case enumerate runtimes WSLc, native WSL, ordinary Linux process container/Docker, separately managed VM, unknown runtime. Map INELIGIBLE=0, HOLD=1, ELIGIBLE_SCOPED=2. Linear penalty is absolute category distance divided by 2. Reviewer A counts: I=5, H=30, E=0. Reviewer B counts: I=5, H=29, E=1. The only differing cell is K1/native WSL (A=HOLD, B=ELIGIBLE_SCOPED); all other 34 cells match. Formula kappa_w = 1 - Do/De.

## Counts and limits

- WSLc/container/Docker/network/process/filesystem/memory operation: 0.
- Candidate execution and runtime probes: 0.
- Independent classifications: 2 isolated agent reviewers; no author reconciliation of M3.
- Retries: 0.
- This result does not satisfy the frozen pass gate; no PASS label, security, performance, parity, memory-relief, or OOM-prevention claim is made.
