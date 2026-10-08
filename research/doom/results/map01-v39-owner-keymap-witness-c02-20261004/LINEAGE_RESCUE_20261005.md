# C02 audit lineage rescue — 2026-10-05

## H / T / D / C / U

- **H:** The retained C02 virtual-X keymap result can be re-audited without rerunning its candidate, while the supplemental auditor fails closed for malformed roots and invalid JSON and preserves the prior v2 report.
- **T:** Re-run the source-bound v2/v3 audit tests against retained raw data; run v3 in ordinary and optimized Python. No candidate, X server, game, model, or GUI action is started.
- **D:** Both auditor suites pass in normal and optimized mode; the v3 report has no failed checks; the pre-existing v2 manifest remains byte-valid.
- **C:** This checks saved virtual-X11 evidence, temporal ordering, and report-path behavior only.
- **U:** It does not establish physical key state, application/game effect, live control, task usefulness, recovery, or a product/runtime claim.

## Lineage and disposition

- Initial package base: `f32f0fd3d6e171b6d010b1f9782d0152c88cd39c`; before opening review, the rescue branch was rebased without conflict onto `54b07b41321ad1e0c4c9c6a37c8501520aa52e77`, then rebased again onto `ff677c7fc04ba72923ee375527ae39489728a0bd` after additional main merges. The focused suite and both manifest checks were rerun on `ff677c7`.
- The retained v2 fail-closed package came from `research/59-c02-admission-audit-v1`, head `6fa91cd31b8638b13ec2f511207ef926934e1542`.
- The sibling v3 addendum was PR #7435 head `4295b925aaf88efa6f5ac8a0c7b90a27e16df8dd`, based on `4346b4c92c44593ef26ea366e1d9f8234f580bf6`. It lacked the later v2 CLI hardening; its v3 report was regenerated against the retained v2 helper without rerunning the candidate.
- The earlier v2 report and `AUDIT_V2_SHA256SUMS.txt` were not edited. Candidate raw SHA-256 remains `80deae01ca6167c91c66e70d725be290b7959750dc1c76e1f344d9f18014e453`.

## Verification

- `python -B -m unittest -v test_audit_temporal_v3.py test_audit_temporal_v2.py test_audit.py`: 24 tests passed.
- `python -O -B -m unittest -v test_audit_temporal_v3.py test_audit_temporal_v2.py test_audit.py`: 24 tests passed.
- `python -B audit_temporal_v3.py` and `python -O -B audit_temporal_v3.py`: scoped v3 PASS; report bytes identical, SHA-256 `628f51226936640aa53351cc9ddfafc7e910dab8ce359645cacf1c6cc2694cb3`.
- `python -B -m py_compile audit_temporal_v3.py test_audit_temporal_v3.py audit_temporal_v2.py test_audit_temporal_v2.py audit.py test_audit.py`: PASS.
- `shasum -a 256 -c AUDIT_V2_SHA256SUMS.txt`: every listed target PASS.
- `git diff --check` on the new audit code/tests: PASS. The complete staged archive has one whitespace diagnostic, a final blank line in the byte-preserved `sources/input_transition_owner_v3.py` snapshot; it was not normalized because it is frozen source evidence.

OrbStack was available, but inspecting cached `python:3.12-slim` failed with `operation not supported` on a containerd content blob. No image pull, container launch, prune, or daemon state change was attempted. Container validation is STOP; the tests above are host-side.

This rescues an archival experiment/audit lineage; it is not a new candidate experiment or evidence for live Issue #59 control.
