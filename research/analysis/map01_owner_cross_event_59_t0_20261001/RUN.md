# Run ledger

## Freeze

- Frozen main: `2b899413d30fcee0ce97e7c69d83f7b2f69e89dd`.
- Workflow blob: `45279028918eff71332e627b1f783dfb11d27e49` (`.github/workflows/map01-measurement-integration-live-04.yml`).
- Owner-helper blob: `f07f928f67a7a6c670d399efb23d67246506c802` (`research/orchestration/o3-g7/global-owner/formal_allocation_global_owner_v1.py`).
- Frozen pre-execution SHA-256: `fixture.json` `F17953DA59D6B86DCED430783FEF8BFC16DCB9B53157E1BEC70B46A774A370AC`; `candidate.py` `CB762DE43411497D754CDBB389B2CDB35B5FE7BD020D89B3A2BE4AB6C4ABA026`; `auditor.py` `E5D0ECE96C352D40B04D59DC43B63E7433F81D4AACF87406706602241BD8E4E3`; `test_construction.py` `17090E6A9BE422B78D1AC4329D44279D8419197FFBB569C5C0DE5186648245E4`; `PLAN.md` `A2D494A18F436A31597C19FEADCFA656034B3206C7CD86CE7659A04D9FBFC51F`.
- Actual run anchor: `34971205791`, completed `push` on `main`, workflow `.github/workflows/map01-measurement-integration-live-04.yml`, head `e947b9809a3449de837e45211a4cb416d990279a`. GitHub Actions run API read confirmed these fields. No second run was dispatched or observed.
- The `workflow_dispatch` row in `fixture.json` is synthetic (`90000000001`), uses the same path/allocation ID and main branch, and is not an actual GitHub Actions run.

## Construction checks before formal candidate

- Environment: Windows host CPU, CPython 3.12.10; no container/GPU/model/game/GUI/input/network request.
- `python -m unittest -v test_construction.py` from the package directory: 4/4 passed.
- `python research/orchestration/o3-g7/global-owner/test_formal_allocation_global_owner_v1.py`: 12/12 passed.
- `python -m py_compile candidate.py auditor.py`: passed.
- `git diff --check`: passed.
- Process deviation: the first construction-test invocation passed a repository-relative path to `unittest` from the repository root and failed with `ModuleNotFoundError: auditor`; no candidate or auditor ran. Re-invoking from the package directory passed 4/4. This command correction is retained and did not alter the scientific fixture or candidate.

## Formal invocation ledger

Candidate command (one invocation):

```powershell
python research/analysis/map01_owner_cross_event_59_t0_20261001/candidate.py --repo-root . --out research/analysis/map01_owner_cross_event_59_t0_20261001/candidate_output.json
```

Independent audit command (one invocation only after candidate exit 0):

```powershell
python research/analysis/map01_owner_cross_event_59_t0_20261001/auditor.py --candidate research/analysis/map01_owner_cross_event_59_t0_20261001/candidate_output.json --out research/analysis/map01_owner_cross_event_59_t0_20261001/audit.json
```

- Candidate ran once, exit 0; output `candidate_output.json` SHA-256 `5C8B719A5BD531C6826412D8EC165768A420A4D33DAFDC1C15BB78A6FECBC0DD`. Both the actual anchored push row and synthetic dispatch row independently returned `PASS_CANONICAL_GLOBAL_OWNER` and `may_enter_formal_step=true` from the exact frozen helper.
- First auditor command was malformed (`--repo-root .`, an unsupported option), exit 1, before executing the oracle or writing output. This invocation error is retained; it was not treated as an oracle result.
- Correct independent audit ran once, exit 1 by design; output `audit.json` SHA-256 `3633393E8A424361832FF39FFF3DAE848B182B9D56F56FCEB0482C7BDA60D2F7`; disposition `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER`, with two admitted IDs `[34971205791, 90000000001]` and one invariant violation `multiple-events-admitted-for-one-versioned-allocation`.
- Formal disposition is a deterministic synthetic source-composition counterexample only. It does not assert or imply an actual duplicate dispatch/run.

## Resource / external-effect record

- Docker Desktop was present and its UI showed `Engine running`, `No containers are running`, 39 listed existing containers, approximately 67.06% engine CPU, 5.15 GB engine RAM use, and 21.10 GB disk use. Existing stopped containers were left untouched.
- A bounded `docker version` probe timed out after 7 seconds. No Docker CLI command established inventory/ownership or launched a container.
- Current #5085 coordination evidence records OrbStack `STOP_ORBSTACK_CONTEXT_OCCUPIED` after finding nonterminal container `98821e10d064` with unknown owner. No access, stop, cleanup, or mutation was performed.
- No GPU, Docker/OrbStack container, network, GitHub Actions dispatch, model/provider, game, GUI, OS input, or task effect was used by this study.
