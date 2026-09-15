# Golden offline dependency closure v1

Status: **FAIL — current supplied wheelhouse does not close the frozen runtime pins.**

Immutable base: `a3ee6b2fd0cab11c39b6be874fef19ed27dad785`.

This is a release-packaging experiment only. It does not change runtime semantics, model behavior, GUI control, retained research allocations, or `runtime/requirements-golden.txt`.

## Experiment

A fresh Python 3.13.5 venv in the disposable Linux container attempted:

```bash
python -m pip install --no-index \
  --find-links=<supplied-wheelhouse> \
  -r runtime/requirements-golden.txt
```

The supplied wheelhouse contained 12 wheels. The checker also compared every exact pin against wheel filenames before invoking pip.

## Result

Only **2/9** frozen direct pins have an exact version in the supplied wheelhouse:

- PASS: `python-xlib==0.33`, `six==1.17.0`
- version mismatch: `Pillow==10.2.0` vs `12.3.0`
- version mismatch: `numpy==1.26.4` vs `2.5.3`
- version mismatch: `openpyxl==3.1.2` vs `3.1.5`
- version mismatch: `et-xmlfile==1.1.0` vs `2.0.0`
- absent: `jsonschema==4.10.3`, `attrs==26.1.0`, `pyrsistent==0.20.0`

The fresh install failed with exit 1 after **285.552 ms** at the first unresolved pin, `Pillow==10.2.0`.

## Interpretation

This disproves only the proposition that the **currently supplied wheelhouse** is a self-contained exact-pin installer for this Python 3.13 container. It does **not** prove that the documented supported WSLg host fails with normal network/package-index access, and it does not justify changing dependency pins without a compatibility test.

The release contract must choose one of two explicit paths:

1. **Self-contained/offline artifact:** build a wheelhouse for the frozen pins and the supported target Python ABI, then rerun this gate and `doctor` from a fresh venv.
2. **Online supported-host setup:** do not present the current wheelhouse as offline installation evidence; freeze the WSLg host/Python version and retain one real networked `setup-golden-demo-v3.sh` + `doctor` run.

## H / T / D / C / U

**H.** The supplied wheelhouse closes every exact pin required by the golden setup script.

**T.** Parse all exact pins, compare against wheel versions, then run one fresh-venv `pip --no-index` installation with no retry.

**D.** **FAIL_OFFLINE_EXACT_PIN_CLOSURE**: 2/9 exact matches; pip exit 1.

**C.** A different wheelhouse built for the frozen pins, or an online supported WSLg setup, may pass. This failure is a packaging/ABI closure result, not package API incompatibility evidence.

**U.** The container is Python 3.13.5/Linux x86_64, not the final supported WSLg acceptance host. Networked index availability and the final host Python ABI remain unmeasured here.

Machine-readable result: `release/offline_dependency_closure_v1/result.json`.
