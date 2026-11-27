# #8887 — common-mode non-identifiability A01

Status: prospectively frozen, narrow impossibility control. This is not the full factorial T0 in #8887 and does not validate Dawid–Skene, Hui–Walter, a dependence-aware estimator, GUI checkers, or action authority.

## Question and structural point

Can agreement alone identify checker accuracy when the checkers may share an unobserved evidence lineage? A shared parser/source can make every checker emit the same bit. With no trusted gold labels or externally established independence/lineage contract, the same observed panel may be compatible with different checker accuracies. The two worlds below intentionally have the same observed checker matrix and the same true-label prevalence; only their hidden truth-to-output coupling differs.

This is a transfer of the diagnostic-testing identifiability boundary, not a new latent-class algorithm. Hui & Walter (1980, DOI [10.2307/2530508](https://doi.org/10.2307/2530508)) rely on conditional independence for their two-population identification design; Dendukuri & Joseph (2001, DOI [10.1111/j.0006-341x.2001.00158.x](https://doi.org/10.1111/j.0006-341x.2001.00158.x)) study models that allow conditional dependence. The recent `judgepanel` software explicitly documents correlated-judge failure as a limitation ([Zenodo v0.1.0](https://zenodo.org/records/21809474)). None validates GUI effect checkers.

## H / T / D / C / U

- **H:** The same no-gold checker matrix can be compatible with materially different true checker accuracies under different, plausible truth/error couplings. Therefore agreement cannot identify accuracy without additional assumptions or lineage evidence, and a safe no-gold report must abstain from an accuracy claim in this fixture.
- **T:** Eight fixed binary rows and four checkers. The candidate sees only checker outputs. A separately implemented auditor evaluates two hidden worlds: (A) truth equals the shared output (all checkers 100% accurate); (B) truth has the same 50/50 prevalence but only four of eight labels match each checker (50% accuracy). Compare all candidate-visible fields and check fail-closed report behavior. Run candidate once, then auditor once, under native Windows CPython with the standard library only. No WSL/WSLc/Docker, model, GUI, network, participant, or external effect.
- **D:** `PASS_COUNTEREXAMPLE_ONLY` iff candidate-visible observations and summaries are identical in both worlds, truth prevalence is equal, accuracy differs by at least 0.40, the candidate reports `UNIDENTIFIABLE_WITHOUT_INDEPENDENCE_EVIDENCE` with no point accuracy/confidence claim, the independent auditor reconstructs every value, and all frozen raw-input mutations are rejected. `FAIL_CONTROL` for an observable mismatch, wrong reconstruction, false accuracy claim, or accepted mutation. `HOLD` for source/result custody or audit failure. This does not pass the whole #8887 T0.
- **C:** A defensible external conditional-independence guarantee, verified source-distinct checker lineage, or an independently adjudicated reference subset could distinguish the worlds and support a narrower reliability statement. In that case, an explicit-assumption latent-class method may be useful.
- **U:** One eight-row constructed common-mode case. No finite observational test can diagnose every possible dependence structure; a pass is an impossibility/control result for this fixture, not evidence that any actual repository checker is correlated or inaccurate.

## Freeze

- Base main: `964c9197d5083ab55ea7fdc9105427623e89e677`
- Branch: `research/8887-no-gold-identifiability-a01`
- Allocation: `8887-common-mode-observational-equivalence-a01-20261012-01`
- Candidate: `candidate.py`; independent auditor: `audit.py`
- Candidate output path: `result.json`; auditor output path: `audit.json`
- Truth world A: `00001111`; truth world B: `00110011`; observed bit is `00001111` for each of four checker columns.
- Both worlds have 4/8 positives. World A yields per-checker accuracy 8/8; world B yields 4/8. Candidate code receives no truth-world input.
- First outcome is authoritative; no candidate/auditor retry or post-result source change.

## Provenance boundary

This execution avoids the currently gated shared WSL/WSLc lane. Its runtime is ordinary local Windows CPython, not a container, and is used only for a tiny standard-library finite control. It makes no claim about memory relief, speed versus Docker/WSLc, runtime parity, or migration readiness.
