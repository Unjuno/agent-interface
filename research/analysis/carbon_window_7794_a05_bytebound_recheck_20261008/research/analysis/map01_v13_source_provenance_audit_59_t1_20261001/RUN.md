# Run ledger

## Freeze

- Current-main commit: `c7346fe1ad0c0d40254c6aa7898a8ed6de76c0dc`.
- Preregistration blob: `88dddea060ad1434a8bc7d67469382928a70ddd7` at `research/doom/map01_measurement_integration_live_v2_prereg.json`.
- The frozen preregistration still names historical allocation `map01-measurement-integration-live-02` / base `7356970b15406c74bd2b404327f39c2e6b546022`. No run uses that allocation.
- Candidate and auditor derive the checkout root from `Path(__file__).resolve().parents[3]`; formal commands run from this package directory with no `--repo-root` override.
- No matching T1 branch/path existed in GitHub branch/code search before this freeze.
- Local host CPU / CPython 3.12; exact Git objects already fetched before the freeze. Candidate/auditor do not access network.

## Pre-formal construction checks

- `python -m unittest -v test_construction.py`: **5/5 PASS** before the one-shot source read.
- `python -m py_compile candidate.py auditor.py`: PASS.
- `git diff --check`: PASS.
- `candidate_output.json` and `audit.json` were absent before the candidate invocation.

## Candidate

- Command, from the package directory: `python candidate.py --out candidate_output.json` (one invocation; no root override).
- Exit 0. The script-derived root resolved the repository checkout and the candidate read the exact frozen Git object commit.
- Preregistration raw blob SHA-256: `edb9da723a0c958a75c514eebdb7b32f6e1aca1895892690292d11edfeec7334`; blob OID `88dddea060ad1434a8bc7d67469382928a70ddd7`.
- Historical preregistration identity is `map01-measurement-integration-live-02`, base `7356970b15406c74bd2b404327f39c2e6b546022`; this remained historical and was not invoked.
- Candidate covered **14/14** paths from the exact union of the two preregistration hash maps. All 14 Git-object SHA-256 values matched their unique pins. Raw candidate SHA-256: `072B2506312B09F86E069DD647731151B61110BD92F2F0AB199803E6995E7E25`.

## Independent auditor

- Command, from the package directory: `python auditor.py --out audit.json` (one invocation after candidate exit 0).
- Exit 0; independent raw-only verification returned `PASS_SOURCE_CLOSURE_ONLY`, 14 independently verified paths, `drift_paths=[]`, `errors=[]`. Audit output SHA-256: `676A047A88907D9FED40469784952F0E713D25567BFFC3AAF2929B320CE8ABA6`.
- After formal execution: `python -m py_compile candidate.py auditor.py`, `python -m unittest -v test_construction.py` (5/5), and `git diff --check` all passed. Candidate and auditor were not rerun.

## Exclusions / authorization

This is only a source-closure audit on the frozen snapshot `c7346fe1ad0c0d40254c6aa7898a8ed6de76c0dc`. No fresh live allocation or exclusive runtime lease is recorded for this task. Docker/OrbStack inventory is still UNKNOWN; no container, game, model, GPU, GUI, input, or Actions dispatch is used. Even a source PASS does not validate a current-main session or authorize live telemetry/recovery efficacy.
