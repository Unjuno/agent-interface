# Issue #5309 pairwise identifiability A02 — scoped method PASS

## Disposition

`PASS_METHOD_SCOPED` for the frozen finite authored model only. This is a distinct A02 successor allocation. A01 remains `FAIL_AUDIT_CONTRACT_INVALID`; it was neither modified nor rerun. No GUI, model, live authority, product, task-utility, or real safety claim is made.

## H / T / D / C / U

- **H:** Generic one-step entropy reduction and repeated success on a benign branch can leave hidden states with incompatible safe commits observationally equivalent; exhaustive bounded pairwise distinguishability can detect the alias and yield `UNKNOWN/YIELD` without granting authority.
- **T:** Candidate and independent oracle ran as separate host Python stdlib processes over four equally likely states and five pairwise scenarios: mode alias, separator available, no separator, expiry before separator, and one-step null. Five same-branch routine successes, proposal/admission/execution/observation separation, fixed exogenous opportunities, and no-action counterfactual were retained.
- **D / result:** `PASS_METHOD_SCOPED`. Independent audit found exactly 1.0 bit of generic information gain while both same-mode benign/hazard pairs remained aliased; all five routine observations also left them aliased. Pairwise oracle returned `UNKNOWN/YIELD` for both mode aliases, no-separator, and expiry-before-separator; it found `witness` for the separator-positive and one-step-null controls. Authority grants=0; refused-observation leaks=0. The independent opportunity reconstruction found two displaced opportunities (one for each hazard state) after `probe_mode`, versus both opportunities preserved in each matched no-action counterfactual.
- **C:** Existing explicit safe probes, freshness/risk gates, or a simpler task-only policy may suffice; the pairwise layer may be redundant or costly. Authored states/actions may overstate real alias frequency.
- **U:** Completeness is limited to the frozen state/action/horizon model. No global impossibility, UI transfer, nonstationarity, live safety, task utility, latency, or product behavior is established.

## Freeze and execution

- Main: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Python: 3.14.5; standard library only.
- Candidate formal invocation: 1/1, exit 0, stderr empty; raw SHA-256 `38dac3760d04b741e491c9e49412ec9778f976b20967edcfa2b53c2c7073d9e1`.
- Independent auditor formal invocation: 1/1, exit 0, stderr empty; audit SHA-256 `283008bb2f0b0968418974805e26a3ae01967330daaeaf1c8c6b3d8e23dc8b76`.
- Formal retries: 0. No Docker/OrbStack invocation occurred for A02: OrbStack inventory continued to fail on containerd `operation not supported`; Issue #5309 explicitly permits a no-container first rung. This host run did not enforce OS-level network isolation; neither script makes network calls.
- Construction tests before freeze: behavioral positive/negative controls passed, including equal-history, valid separator, expiry boundary, refusal censoring, authority escalation, and four corrupted-raw controls.

## Reproducible commands

```text
python3 test_construction.py
python3 candidate.py > candidate-raw.json 2> candidate.stderr.txt
python3 auditor.py candidate-raw.json > audit.json 2> auditor.stderr.txt
python3 -m py_compile candidate.py auditor.py test_construction.py
```

The formal candidate and auditor commands were each executed exactly once. Post-run checks may verify saved files/hashes, but must not replay those commands under this allocation.
