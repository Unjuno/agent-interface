# One-shot T0b run log

- Issue/allocation: #6089 / `OBS-LOSS-ROBUST-TUBE-6089-T0B-HOSTCPU-20261002-01`.
- Frozen main: `c000d85275a6689035a5bd7f5b75803b095c8299`; frozen source commit: `4e22075e095c09d7228f552a458966049eba9915`.
- Runtime: Windows host CPU, CPython 3.11.9, stdlib only.
- Construction: `python -m unittest -v test_method.py` — 6/6 passed, including five corruption controls.
- Immediate pre-start gate: main and branch matched freeze; all seven source hashes matched; candidate/audit outputs absent. CPU inventory returned no numeric load sample (unknown, not interpreted as idle).
- Candidate: `python run_candidate.py candidate_raw.json`; one invocation, exit 0. Output creation observed 2026-10-02 08:32:12 UTC; file size 19,987 bytes; SHA-256 `63f2f8acc696130b0c2db10619dd32c513977e342a946115597e3797e511e528`.
- Auditor: separate process `python run_audit.py candidate_raw.json audit.json`; one invocation, exit 0. Output creation observed 2026-10-02 08:32:17 UTC; size 71 bytes; SHA-256 `5929fefe3cce62c46c54aa79434654bfd175a5a16fa51fe6e429b2501c05ccfc`; status `PASS_METHOD_SCOPED`, errors `[]`.
- Rows: 7. Candidate outcomes: k=0 selected horizon 5 matching base; k=1 and k=2 selected 4; one-miss and delayed-old-generation optimistic A controls were unsafe; B release-on-absence was safe in the fixtures; invalidation and unsupported bound yielded; beyond-k stress remained uncertified.
- The first post-run ref check observed main `87d5699dbdc94b48ca5664d80f8bcfdb4b76e441`, newer than the frozen base. The exact timing of that main advance relative to candidate/audit completion was not captured; the immediate pre-start check matched the frozen SHA.
- Resource accounting: candidate/auditor 1/1, retries 0; model/GPU/CUDA/training/adapter/container/network/GUI/game/input 0.
- STOP criteria: none observed. No result was overwritten and no candidate/auditor rerun occurred.
