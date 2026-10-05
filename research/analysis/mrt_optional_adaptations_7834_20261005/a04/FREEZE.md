# A04 freeze — MRT-7834-A04-20261005

Prospective issue comment: 5986448843
Base main at freeze: 6f34c5c0c5bc3116d8e7c25f29aa1b92cc4a01b
Candidate 770b9f7c38a61c5bed08d9626ecbec4dfe466f9b; auditor ad257ce38bb0453cd976c88996a11dbb36224f47; fixture dd30196595561d9f0d1fe59e05086f09c40bded7; runner 062eab2ba87fcb0ec8d124886e09ce641acd3502.

H: Known current assignment and observation propensities recover marginal proximal excursion contrasts for arms 1 and 2 vs arm 0 under three-arm, history-varying assignment, pre-treatment second-step eligibility, known outcome censoring, non-execution and one-step carryover. Keep distal policy outcome separate. Unsupported assignment/observation, unknown missing window, post-treatment eligibility, interference, and beyond-horizon carryover are NONIDENTIFIABLE.

T: Two fixed session types U=0,1. t1 p=[.5,.25,.25]. t2 is eligible iff t1 assignment is nonzero; after arm1 p=[.25,.5,.25], after arm2 p=[.2,.3,.5]. Independent known outcome observation q=.8. Carryover for previous arm 0/1/2 is 0/.5/1. Baseline=1+2U+previous. Effects: arm0=0; arm1=2+U+.5*I(previous=2); arm2=-1+2U+I(previous=1). Execution logged separately: assigned != ((U+previous+1) mod 3). Distal policy score=10+U-1.5*A1-.75*A2 when t2 is eligible. Independently enumerate exact rows, marginal IPW/oracles, observation rate, execution fractions, distal values, non-identifiability gates, 17 mutations. Candidate/auditor max 1 each, retries 0.

D: 2,600 exact rows; eligible weight 3 within 1e-12; observation rate .8; arm1/0 effect 31/12 and arm2/0 effect 1/6 within 1e-12; distal U0=8.44375 and U1=9.44375 within tolerance; execution fractions match; all controls NONIDENTIFIABLE; no task-success claim; 17/17 mutations rejected. Any mismatch is FAIL_METHOD. Pre-candidate environment/source failure is STOP_ENVIRONMENT, no retry.

C/U: One authored finite case only. No empirical MRT, finite-sample guarantee, effective sample size, moderator, user, consent, safety, long-carryover, GUI, task, or external-validity result.

Frozen candidate command:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a04-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a04-20261005\candidate-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 node /src/runner.js candidate

Frozen auditor command:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a04-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a04-20261005\candidate-out:/input:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a04-20261005\audit-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 node /src/runner.js audit

Qualification: freeze text says five controls, while its exact fixture blob lists six distinct controls. Both frozen functions tested all six, each NONIDENTIFIABLE. The count mismatch is preserved by append-only comment 5986498125; no source/result rewrite or rerun. Pre-freeze construction probes are separately retained in CONSTRUCTION.md.