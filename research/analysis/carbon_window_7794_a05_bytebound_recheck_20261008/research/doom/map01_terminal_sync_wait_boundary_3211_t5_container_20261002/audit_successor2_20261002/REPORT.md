# T5 retained-trace independent audit — successor 02

## H/T/D/C/U and result

- **H:** A separately authored verifier can parse the immutable T5 event sidecars using their literal `\\n` delimiters, check the full frozen input manifest, reconstruct the four cases and retain a result in one offline WSLc run.
- **T:** Allocation `MAP01-TERMINAL-WAIT-BOUNDARY-3211-T5-AUDIT-SUCCESSOR2-20261002-01`; immutable source commit `49f2940ce79bd48bab376d8825f07bd8535a7361`, PR #6294 head; Python 3.12.14 on cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; WSLc `--pull never --network none --cpus 1 --memory 512M`; input and auditor source read-only; distinct output mount. Candidate, original T5 auditor, and #6306 failed auditor were not invoked. New auditor once; retry 0.
- **D:** `PASS_AUDIT_SUCCESSOR2_SCOPED`. All 13 `SHA256SUMS` entries matched before execution. The independent verifier matched frozen source identities and T5 receipt identity, reconstructed each literal-delimited sidecar and matched event arrays, SHA-256 and byte counts, checked case IDs/dispositions/timing/timeout classes and verified child-reaped/reader-joined flags for all four cases. It wrote `AUDIT.json`; exit 0.
- **C:** This is an independent audit of already-retained synthetic `JsonSession.wait()` records only. The original T5 execution remains `HOLD_AUDIT_ARTIFACT_WRITE_PATH_PREEXISTED`; neither it nor the failed #6306 auditor was retried or relabeled.
- **U:** No MAP01/gameplay efficacy, original recovery-arm cause, GUI/model/provider/input, memory enforcement, Docker parity, iteration benefit, or product claim. WSLc warned that swap-limit capabilities or cgroup mounting are unavailable. This does not meet Issue #3352's separate requirement for a representative roadmap workload.

## Identity and verification

- New auditor SHA-256: `EAEB77685949B3218BAF714CAD4CCD2E48261544B508DAA4C4C14E28D8E6CD04`.
- Test-first construction source SHA-256: `5E79D50E19255C2D5A246C7C8B13886DF3B4A0EE9225C264EB6C5C6E0158D0D0`; 5 host tests passed before the formal audit.
- Candidate receipt SHA-256: `d19e9da7be4d188c7309d426494f5c845fbeb06b9c55f190bdd4b4dc8ffc2a43`.
- T5 freeze SHA-256: `56daa018be6eeb463e621855b97851270fdee73676d74b830eb511b70c5ce204`.
- Audited cases: within-bound matching terminal; wrong-ID timeout; absent-terminal timeout; matching-but-late terminal timeout. All recorded cleanup booleans true.
- The post-run WSLc stats listing was empty; `--rm` was used. A pre-existing unrelated exited migration container was left untouched.

The audit source is self-contained and imports none of the T5 candidate, T5 auditor or #6306 auditor. The T5 evidence is sourced from the exact PR #6294 head, not asserted to be on main. The audit result is not a promotion of PR #6294 or closure of #3211/#3352.
