# Issue #6536 T0 result — synthetic claim-scoped clip-to-trace audit

## H / T / D / C / U

- **H:** On a finite planted fixture, a claim-scoped map and independent raw-only audit can accept honest scoped excerpts while rejecting unsupported whole-run, time-alignment, task-outcome, and control-attribution claims that a clip/caption, master link, or hashed EDL alone can accept.
- **T:** The frozen allocation `CLIP-TRACE-6536-T0-20261002-01` compared A (clip + caption), B (clip + master link), C (hashed EDL only), and D (claim-scoped map + independent auditor) over nine cases: two honest excerpt claims and seven planted unsupported/forged claims. Candidate and auditor were separate implementations. Full commands and source/input identities are in `FREEZE.json`; the initial output was absent.
- **D:** `PASS_METHOD_SCOPED` required independent reconstruction of every row/arm, acceptance of both scoped-positive claims, zero false accepts by D, and rejection of five frozen corruption controls. All conditions passed. This is a finite method result only.
- **C:** A clear uninterrupted master plus trace may be simpler and sufficient for human review. The baseline arms are intentionally limited evidence contracts; the authored synthetic fixture may make boundary faults easier to expose than real video/transcoding does.
- **U:** Synthetic frame identifiers, clocks, events, and independent terminal receipt only. No real video or trace, C2PA signature/validator, GUI/game/model/input, actual DOOM result, public editing/claim, user study, or end-to-end task value was tested. Hashes establish byte identity, not capture truth.

## Execution and result

- Candidate: one invocation, exit 0, nine rows. Fixture SHA-256 `070133cad5ebe31db82962bfe0ea3da1993262ca12e63bcb750fbb324e6500c3`; master digest `550be92b008a34435e3273de52d4d2b8928f9be1e0f820cee99f9df5dc5d68ac`.
- Independent raw-only auditor: one invocation, exit 0, `PASS_METHOD_SCOPED`, nine reconstructed cases, two supported claims accepted, zero audit errors.
- False acceptances among seven unsupported claims: A=7, B=6, C=2, D=0.
- Five controls rejected: forged master digest, unmapped interval digest, shifted-clock decision, missing release lineage, and false-clear decision (5/5).
- Construction tests: 5/5 passed before freeze and again after the formal run; candidate/auditor compile checks passed.
- Local CI: restored the repository's exact pinned Analysis Index workflow source (`b19000e0…`) as its provenance step; analysis index verified 532 retained result/failure directories; all 17 existing workflow test suites passed (104 tests), plus this package's five tests (109 total). The two nested suites ran from their declared working directory. `.github/workflows/analysis-index.yml` was restored unchanged afterward.
- Platform: Darwin 25.6.0 arm64, CPython 3.14.5, stdlib only. WSLc is unavailable on this host; no container was used because the Issue makes WSLc optional and this finite T0 needs neither Engine API nor special isolation. No model, GUI/game, user asset, or real media was accessed.

Raw and audit JSON are retained unchanged at `RAW.json` and `AUDIT.json`. The frozen inputs, allocation gates, source SHA-256 values, and command argv are in `FREEZE.json`; `SHA256SUMS` binds the complete evidence package. Historical Issues #58/#59/#2679 and their media/trace assets were not modified or accessed.
