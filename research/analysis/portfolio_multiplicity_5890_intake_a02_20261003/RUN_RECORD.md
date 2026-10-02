# A02 formal run record

- Allocation: `PORTFOLIO-MULTIPLICITY-5890-INTAKE-A02-20261003`; owner task `01a0b990-3d17-72f1-a908-9a2072104ce5`.
- Frozen base main: `f8e71fc777100281c67a51233b222334fada2863`.
- Branch: `research/5890-intake-funnel-a02-20261003`; freeze/source commit before launch: `5dcde3b774bab4107d11f98cb78355e661719de8`.
- Environment: Windows host, CPython 3.11.9, standard library only. No WSLc, container, GPU/CUDA, model, network, GUI/game or input.
- Preflight: 5/5 construction tests passed on inline-only fixtures; local and remote branch heads matched; candidate and audit outputs were absent; frozen source/input hashes matched; C: had 37.53 GiB free at the bounded pre-run check. Three Python processes were observed (PIDs 17100, 19052, 30360; existing processes were not stopped or modified). The 8.7 GB process was left untouched; this allocation was a small host-CPU run.
- Formal window: 2026-10-02 17:40–18:00 UTC.

## Invocations

1. `python research\analysis\portfolio_multiplicity_5890_intake_a02_20261003\candidate.py` — exactly once, exit 0, 2026-10-02 17:40:32 UTC. Counts: 25 total rows; 16 screened-out/not-tested; five started opportunities; four eligible statistical-family members; four deterministic checks; one abandoned started negative retained.
2. `python research\analysis\portfolio_multiplicity_5890_intake_a02_20261003\auditor.py` — exactly once after candidate exit 0, exit 0, 2026-10-02 17:40:38 UTC. Exact replay `true`, 25/25 rows, five of five frozen corruptions rejected, disposition `PASS_METHOD_SCOPED`.

Candidate invocations 1; auditor invocations 1; retries 0. No post-result source or fixture changes.

## SHA-256

| Artifact | SHA-256 |
|---|---|
| `PROTOCOL.md` | `4e99e478b3f778f94016c08d650d695ae80195cd4682a79943e639dd7c788eff` |
| `formal_input.json` | `f8063007a064962d906bea872bded630c9a74e873b551c7c74b6d433ef5425b7` |
| `candidate.py` | `6090226f02a6d5f895837f4857408f69a9ab299293a7dde30ad3cd63109291f2` |
| `auditor.py` | `6cb79851f6b13d380528b63f3414a26551fd36599ba2668afe796fdb3751d914` |
| `test_method.py` | `c1f6b695a21b8f5d012da8f291d2d3c1642daec4605e7a26220124ee38164ae0` |
| `candidate_raw.json` | `dc566834352f3d1ed9c9e2f9b58ebaee42ac212aba6eb8cf427795ef47cfbb49` |
| `audit.json` | `4ca9e8acd2b16c58059fac9a1d7d24bddd5d3cda80120e155f125908f0a783ac` |

The exact input hash and pre-run source hashes match `FREEZE.json`. These hashes identify one synthetic method run and are not evidence of an FDR guarantee or live application behavior.
