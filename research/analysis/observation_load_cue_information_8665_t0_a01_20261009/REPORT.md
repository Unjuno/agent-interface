# Issue #8665 T0 A01 result

- Allocation: `8665-T0-A01-20261009`; frozen source commit `ad0866478d531fbdd4a76cde518568baf941372b`, based on `main` `23d1807ffad8359e0f89421ee2b9bf5783c9d5f4`.
- Candidate: one invocation, exit 0; 256 rows across four regimes × eight matched seeds × eight randomized cells. Raw SHA-256 `57abf1d05c8fd8c0772bfec3394dc306f6a17c2dc96354606d81aa852f38d2a8`.
- Independent raw-only audit: one invocation, `PASS_METHOD_SCOPED`, zero errors; all five frozen mutation controls rejected.
- Finite fixture contrasts: load-only loaded-minus-minimal `-1.000`; transient cue content-by-response `-0.500`; stable control `0.000`; no-information control `0.000`. Classification: `MIXED_SCOPED_FIXTURE`.
- Candidate/source/command identities and runtime details: [`RUN.json`](results/first-outcome/RUN.json). Full raw and audit: [`RAW.jsonl`](results/first-outcome/RAW.jsonl) and [`AUDIT.json`](results/first-outcome/AUDIT.json).

This is a method-level PASS and the preregistered finite synthetic fixture's mixed signature. It shows that the ledger and auditor distinguish a load-only deadline contrast from a content-sensitive response contrast while both controls remain at zero. It does **not** show that GUI observation load affects real computer control. No live GUI, OS input, model, container, or external service ran. It establishes no real OS scheduling effect, mediation, safety, user-tempo benefit, or product result. Issue #8665 and the broader computer-control goal remain open.
