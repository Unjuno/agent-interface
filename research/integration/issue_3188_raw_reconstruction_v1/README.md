# Issue #3188 formal-02 independent raw reconstruction

## H/T/D/C/U

- **H:** The immutable formal-02 truth table has exactly the declared 32 unique Boolean vectors, exactly one all-true `AUTHORIZE`, 31 `HOLD` vectors, and five named negative controls that all remain `HOLD`. The corrected row summary is 37 and the current snapshot is `HOLD`.
- **T:** Independently parse and reconstruct the committed formal-02 `raw.json`; do not import or invoke either candidate auditor. Before interpretation, bind the raw, `PREREG-FORMAL-02.md`, `run.py`, and `audit.py` to the SHA-256 digests frozen in `audit_raw.py`. Enumerate in declared field/product order and challenge bit, row-count, class-label, negative-control and external-digest substitutions.
- **D:** `PASS_RAW_RECONSTRUCTION` requires all four frozen inputs to match, 32/32 unique ordered vectors, the all-true-only admission predicate, all five exact control names with `HOLD`, summary 32 vectors + 5 controls = 37 rows, exactly one `AUTHORIZE`, and every automated corruption challenge rejected. Any mismatch is `FAIL_RAW_RECONSTRUCTION` or a failing unit test.
- **C:** Read-only audit of the already-retained formal-02 allocation only. No candidate execution, CI dispatch, game/model/GUI/X11/input, authority grant, or new allocation. A CRLF checkout is accepted only when transforming CRLF to LF reproduces the externally frozen exact Git-blob digest; no other normalization is performed.
- **U:** This finite audit validates one frozen truth table and the listed challenges only. It is not workflow/CI equivalence, MAP01 recovery efficacy, generalized verifier soundness, runtime safety, or production authority.

## Frozen provenance

The source allocation is preserved under `../issue_3188_source_bound_entry_gate_v1/`, from PR #3731 merge commit `eca4bcc1ee839b80442397e27f238c97d6dd6bb4`. The original allocation's formal disposition remains `HOLD_FROZEN_AUDITOR_DEFECT`; this successor does not overwrite that result.

The first transient raw-only calculation preceded this packaged successor, so the protocol here is an independent reproducibility check of an already observed outcome, not a preregistered first-look experiment. The prior calculation was not used as a test oracle; expected decisions, field order, cardinality and digest are taken from the frozen source/preregistration.

| Input | Frozen SHA-256 |
| --- | --- |
| formal-02 `raw.json` | `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324` |
| `PREREG-FORMAL-02.md` | `a03047ae51adc7ed1ba5d97b295a6bfe8607f0e34933e00cb00172eb27c791b8` |
| candidate `run.py` | `e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822` |
| candidate `audit.py` | `72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d` |

The existing v1 auditor result is preserved as `FAIL_AUDIT` (enumeration order and aggregate row count); the existing v2 independent result is preserved as `PASS_INDEPENDENT_AUDIT`. This package independently reconstructs the raw and does not edit either receipt.

## Reproduce

From the repository root, with Python 3.11+:

```powershell
python -m unittest discover -s research/integration/issue_3188_raw_reconstruction_v1 -p "test_*.py" -v
python research/integration/issue_3188_raw_reconstruction_v1/audit_raw.py . research/integration/issue_3188_raw_reconstruction_v1/RESULT.json
```

This is a native read-only audit, not a Docker result. Docker Desktop was unavailable at the time of this audit; the original OrbStack allocation evidence remains separately labeled and does not satisfy a Docker Desktop-specific gate.

## Observed result

Windows / Python 3.12 native verification: 7/7 unittest methods PASS; standalone result `PASS_RAW_RECONSTRUCTION`; all five corruption challenges rejected; `git diff --check` PASS. Exact output is retained in `RESULT.json`. The first transient reconstruction was exploratory; this packaged run is an independent reproducibility check, not a preregistered first-look result.
