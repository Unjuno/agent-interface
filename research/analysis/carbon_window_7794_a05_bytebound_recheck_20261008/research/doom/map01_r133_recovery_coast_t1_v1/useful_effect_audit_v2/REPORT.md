# Construction v2 result — recovery-arm useful-effect gate

**Disposition: `COUNTEREXAMPLE_SCOPED`.** On the frozen adjudicator, the preregistered target case returned `PASS_DIRECTIONAL_FIXTURE_SCOPED` even though the recovery arm had positive kill/exit in 0/3 pairs and coast had it in 3/3. The recovery arm remained alive at the horizon in each synthetic pair and had strictly lower unsafe exposure; survival dominates the paired progress tuple. Thus this is a counterexample to interpreting the current scoped PASS as evidence of a recovery-arm kill/exit advantage, not necessarily a defect if survival alone is intentionally sufficient.

## H / T / D / C / U

- **H:** The current v2 paired adjudicator can pass without recovery-arm positive kill/exit pairs because it uses a global either-arm useful-event gate and lexicographically prioritizes survival.
- **T:** Five frozen synthetic six-session cases, the exact current adjudicator, one candidate invocation, then a separate raw-only auditor. Candidate and auditor each exited 0; retries 0.
- **D:** Candidate dispositions: target coast-only kill `PASS_DIRECTIONAL_FIXTURE_SCOPED`; both-arm positive `PASS_DIRECTIONAL_FIXTURE_SCOPED`; no-positive-effect `HOLD_NOT_EVALUATED`; no-threat `HOLD_NOT_EVALUATED`; overlapping exposure `UNCERTAIN`. Independent audit found zero errors and rejected all 3 corruption controls.
- **C:** CPython 3.14.5, Darwin arm64, stdlib only; pure deterministic synthetic logic. No container/shared lease, model, game, GUI, input, GPU, or network. The prior v1 fixture-order STOP is preserved and was not rerun.
- **U:** This does not decide whether survival is sufficient task progress, validate the scorer, demonstrate policy usefulness, or show live MAP01 safety/efficacy. It indicates the prospective hypothesis and PASS wording need an explicit treatment-arm-specific task-effect rule or an explicit statement that survival alone is sufficient. No allocation is authorized.

## Reproduction

From this directory:

```sh
python3 -B candidate.py
python3 -B audit.py
python3 -m py_compile candidate.py audit.py
sha256sum -c SHA256SUMS
```

The candidate uses the hash-pinned `decision_rule_construction_v2/adjudicator.py`. The auditor reads only `RAW.json`; it does not import the candidate or adjudicator. Exact output and source/raw hashes are retained in this directory.

The candidate run was host-only rather than containerized because the tested behavior is fully determined pure-Python logic and there was no matching owner-bound container lease. This does not relax any live/container gate for T1.
