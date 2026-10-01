# Issue #5739 T0 — retained first outcome

## Disposition

**STOP_AUDIT_BASE_PIN_MISMATCH; scientific/method result NOT_EVALUATED.**

The one frozen candidate invocation exited 0 and emitted a finite synthetic record with 5 screen rows and 12 matched confirmation rows. The one frozen independent auditor invocation exited 1 with errors=["base main SHA mismatch"]. The auditor source hard-codes base 24f6b7d5f9395105807f981d48db212e6692a6f4, while the preregistration and FREEZE correctly bind the final pre-run main to 8627fb4ad928479be363c3d7754146dfc8afb793. The auditor groups this base-pin error into source_errors, so its source_hashes_match=false field is not a valid source-byte finding; pre-candidate SHA-256 checks and GitHub blob readback had matched all eight frozen source files. No corrected auditor or candidate retry was run.

The candidate's unreviewed raw labels withhold familywise promotion, global-best, and the fastest hard-safety-failing arm. They remain candidate output only; the required independent process did not validate them, so this is not PASS_CLAIM_BOUNDARY_SCOPED and no method conclusion is claimed.

## H / T / D / C / U

- **H:** Not adjudicated. Candidate output alone cannot establish whether the claim-boundary hypothesis passed.
- **T:** One deterministic host-CPU invocation on CPython 3.11.9, Windows x86_64; exact main 8627fb4ad928479be363c3d7754146dfc8afb793; screen/confirmation fixture and oracle SHA-bound before run. Candidate saw screen.json and confirmatory.json; the independent auditor saw the auditor-only sealed_oracle.json. No Docker/OrbStack, GPU/CUDA, model, network, GUI, game, or input.
- **D:** Candidate: exit 0, one invocation. Auditor: exit 1, one invocation, retained STOP_AUDIT_BASE_PIN_MISMATCH. Retry budget 0. Preflight unit tests passed 10/10 before freeze/run; they did not exercise the auditor's file-level base-SHA check. No post-failure auditor tests or corrections were run.
- **C:** Analyst-authored finite outcomes and local standard-library Python only. Pre-run source hash checks and GitHub blob readback verified all 8 frozen source files. The later auditor disposition is a harness/base-pin error, not evidence for or against the method hypothesis.
- **U:** No statistical calibration, exchangeability, live runtime, empirical task effect, actual resource saving, user, or product inference. The raw labels remain unverified until a separately authorized/versioned read-only audit path; the frozen auditor and candidate are not to be rerun.

## Exact commands and raw identity

- Preflight: python -B -m unittest -v test_candidate.py test_audit.py — 10/10 pass (before candidate).
- Candidate: python -B candidate.py — exit 0, once; exact stdout is retained byte-for-byte in STDOUT.bin and CANDIDATE.json.
- Auditor: python -B audit.py — exit 1, once; exact stdout is retained in AUDIT_STDOUT.bin and AUDIT.json.
- Candidate raw SHA-256: 2abbbc32dac1780181f19275cc3b2315aefbd603391748f766199b3f41ae197d.
- Candidate output has 5 screen attempts and 12 confirmation attempts.
- The attempted git diff --check was unavailable because this local scratch directory is not a Git checkout; frozen files were instead checked by SHA-256 and exact Git blob readback before execution.

All outputs, including the audit failure, are retained unchanged. No attempt was made to amend the frozen sources or replace the failed auditor disposition.
