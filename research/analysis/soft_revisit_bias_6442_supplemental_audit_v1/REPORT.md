# #6442 supplemental exact-transcript audit v1

## Result: PASS_RETAINED_TRANSCRIPT_SCOPED

This is a bounded repair of the raw-only audit contract exposed in
[PR #6849 review 5398165654](https://github.com/Unjuno/agent-interface/pull/6849#pullrequestreview-5398165654).
The original A03 raw is valid under a separate exact-transcript oracle. The
legacy auditor nevertheless accepted a declared zero budget and a fabricated
early refusal, so its general reconstruction-integrity claim needed qualification.

`audit_v1.py` independently enumerates only the explicit deterministic A03
two-edge schedule and compares the complete typed row, including budget,
observation/navigation order, justified refusal, observed labels and terminal.
It imports no candidate, policy, fixture or legacy-auditor implementation.
Duplicate JSON keys are rejected before parsing can hide them; output is fresh
and input/previous output are preserved. Input is bounded to 1 MiB. Oversized
input is labeled with a prefix hash only.

On Windows 11 x64 / CPython 3.12.10, the legacy regression run had four expected
failures in nine tests: zero declared budget, fabricated refusal, boolean epoch,
and float budget. The separate CLI construction run exposed two additional
implementation defects (duplicate-key parsing and truncated-input hash labeling);
both first outcomes are retained. After repair, all 13 construction tests passed.
The distinct read-only replay started at 2026-10-03T00:47:28.1428252Z and finished
at 00:47:28.4056317Z with process exit 0, 128 rows and zero errors. Those timestamps
are execution provenance, not a latency benchmark.

| Policy | Stable target successes | Partial/revision target successes |
|---|---:|---:|
| Stateless | 8/8 | 16/16 |
| Hard exclusion | 8/8 | 0/16 |
| Soft revisit | 8/8 | 16/16 |
| Exhaustive | 8/8 | 0/16 |

The soft/stateless tie still demonstrates no incremental soft-policy value on
this authored schedule. No comparator, input, threshold or prior disposition was
changed. This supplemental analytic result is distinct from historical A03
`PASS_METHOD_SCOPED`; it does not upgrade that experiment to GUI/runtime benefit.

## Evidence and input custody

- Input head: `ee38cf1765f465706c9e0355ae41ef31ca4ba057` from PR #6849.
- Input path: `research/analysis/soft_revisit_bias_5756_t0_orbstack_a03_20261003/candidate/raw.jsonl`.
- Exact input SHA256: `c13a98c8b5840697b410e093f4132b9f9b314c8893d1cf6f32a4b889924edbfa`.
- `REPLAY_BINDING.json` was recorded before the separately logged supplemental
  replay; its three source hashes bind auditor, tests and prospective protocol.
- `supplemental-audit.json` and `replay-exit.json` retain the supplemental outcome
  and process receipt. Construction/red-stage logs are retained with local
  workspace paths replaced by `<supplemental-package>` for publication; original
  logs remain in this worker's private outputs. `PUBLICATION_PROVENANCE.json`
  binds original and redacted log hashes. Historical experiment logs are untouched.
- This additive package does not copy or rewrite A01/A02/A03 source, raw, freeze,
  manifest or first audit. It does not alter PR #6849's branch.

## Reproduction

Fetch the reviewed PR head into an isolated clone, then extract the input using
binary Git stdout (avoid text redirection that could alter line endings):

```powershell
git fetch --depth=1 origin ee38cf1765f465706c9e0355ae41ef31ca4ba057
python -c "import subprocess; from pathlib import Path; Path('retained-raw.jsonl').write_bytes(subprocess.check_output(['git','show','ee38cf1765f465706c9e0355ae41ef31ca4ba057:research/analysis/soft_revisit_bias_5756_t0_orbstack_a03_20261003/candidate/raw.jsonl']))"
$env:RETAINED_RAW = (Resolve-Path retained-raw.jsonl).Path
python -B -m unittest discover -s research/analysis/soft_revisit_bias_6442_supplemental_audit_v1 -p test_supplemental.py -v
python -B research/analysis/soft_revisit_bias_6442_supplemental_audit_v1/audit_v1.py --input retained-raw.jsonl --output supplemental-replay-new.json
```

Tests require the exact separately retained input; missing `RETAINED_RAW` is an
explicit setup error, not a skipped success. To reproduce the legacy failing
regressions, set `LEGACY_AUDIT_SOURCE` to a scratch copy of the immutable A03
`audit.py` and `fixtures.py`; no candidate is invoked. Never overwrite prior
audit files or rerun a consumed formal candidate for this engineering repair.

## Scope and delivery

The oracle is specific to these 32 authored fixtures and four frozen policies.
It is not a generic hierarchy validator, proof of dynamic epoch recovery,
authority mechanism, live effect scorer, timing result, safety guarantee or
model/GUI benefit. See `PROTOCOL.md` for H/T/D/C/U and the frozen rejection rules.
No formal candidate, container, WSLc, GPU, model, GUI or physical input ran.
The new tests and auditor are explicit local entry points; this change adds no
workflow or runtime import. Construction requires an explicitly supplied input
path and does not invoke the candidate. No complete repository CI result is claimed.

Local host memory pressure interrupted an unrelated read-only workflow archive
inspection. The verified owned Git archive processes were stopped; no other
worker or formal allocation was interrupted. That infrastructure failure does
not reclassify this already recorded audit result. A reviewable PR remains the
delivery route; FINAL-v5 non-author quorum and current-base combination checks
are required before main integration. This package alone authorizes no merge.
