# T0 run log — PHASE-CONTROL-DELAY-8668-T0-A01-20261009

## Launch record

- Launch record written at UTC: `2026-10-08T19:09:18Z`.
- Source worktree branch: `research/8668-phase-control-delays-a01-20261009`.
- Frozen source commit: `766297bbadd674bb76d5e83968a7aa5e12cb04eb`; frozen main: `23d1807ffad8359e0f89421ee2b9bf5783c9d5f4`.
- Candidate SHA-256: `960ef9c63787788dfb2a2808ce4291dc976438c0b0b42b63a88b4dd85deba80e`.
- Auditor SHA-256: `b6ed0ebcbc1c3674ac6e8bfa822099f0919ed3ec981e4f1cc67ee0ff968ba0e4`.
- Environment: Darwin arm64, CPython 3.14.5, standard library only.
- Preflight: remote `main` equals the frozen base; #8668 is open and unassigned with no comments; GitHub MCP searches returned no matching PR or branch; `run-01/` did not exist.
- Candidate command (one invocation): `python3 -B candidate.py > run-01/candidate.json 2> run-01/candidate.stderr`.
- Auditor command (only if candidate exit is zero): `python3 -B auditor.py run-01/candidate.json > run-01/audit.json 2> run-01/auditor.stderr`.
- Candidate: invoked once; exit code `0`; stderr empty; 481 schedules emitted.
- Raw candidate SHA-256: `9977d26c82ff6c30152b66290c7690856dfcab45e377334f31fd358da20d0678`.
- Auditor: invoked once after candidate exit 0; exit code `0`; stderr empty; status `PASS_METHOD_SCOPED`; errors `[]`.
- Raw audit SHA-256: `a9c11cabef70c3ea75dd585d8a2f3a39af36f81aeed662d06d996b3c33cc49ac`.
- All five frozen mutation controls were rejected. Candidate and auditor completion was observed by `2026-10-08T19:10:26Z`.
- No retry or second candidate invocation.
