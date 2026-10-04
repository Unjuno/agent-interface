# Issue #7436 T0 — route-blind adjudication method probe

This package tests only whether a synthetic packet presenter withholds explicit route canaries until a score commitment. It does not test human assessors or estimate observer bias.

## H / T / D / C / U

- **H:** The presenter can retain the frozen rubric and evidence while removing route/candidate/branch/winner canaries; custody refuses reveal before commitment; seeded packet order is reproducible; all eight preregistered corruptions are effective and rejected.
- **T:** Six synthetic evidence files in three paired strata. Route canaries occur in real source directory/file names, metadata, and summaries. One candidate invocation produces blinded packets and a synthetic score commitment; one independent raw-only auditor reconstructs expected bytes and tests eight mutations. No human, model, GUI, provider, or live route is involved.
- **D:** `PASS_METHOD_SCOPED` only if all six packets retain the rubric and evidence, contain no route canary, the precommit reveal is denied, postcommit mapping matches the escrow, order matches the seed, and all 8/8 effective corruptions are rejected. Otherwise FAIL/STOP as specified in `PREREGISTRATION.md`.
- **C:** A single-process method probe does not provide filesystem/process confidentiality. The synthetic evidence intentionally makes paired route content identical; natural evidence may reveal route identity even after metadata removal.
- **U:** No human-bias estimate, route-favorable false-positive rate, assessor agreement, user preference, deployment recommendation, or T1 result follows. The T1 assessor study still needs prospective sampling, independent assessors, consent/ethics review where required, and precommitted analysis.

## Reproduction

From repository root, after verifying the recorded base/freeze and that `results/` is absent:

```sh
python3 -I -B -m unittest discover -s research/analysis/route_blind_adjudication_7436_t0_a01 -p 'test_package.py' -v
python3 -I research/analysis/route_blind_adjudication_7436_t0_a01/candidate.py
python3 -I research/analysis/route_blind_adjudication_7436_t0_a01/audit.py
```

The candidate and auditor are one-shot formal invocations for this allocation. Do not rerun them to repair outputs. The construction suite is distinct and may be rerun after a separately recorded source change.

Container image inspection hit an OrbStack containerd content-store `operation not supported` error; Podman is unavailable on this host. The deterministic standard-library method probe therefore used the frozen host-only fallback. No claim of container isolation or enforcement is made.
