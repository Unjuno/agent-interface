# Capture availability and parent-region visibility — #4365

**PASS_CAPTURE_VISIBILITY_BOUNDARY_SCOPED**, twelve prospective first sessions; no formal retry, case replacement or frozen-source change. Evidence only; no shared runtime or previous result is changed.

| Interpretation | False clear reports over12 directed cases |
|---|---:|
| Capture-success-only | 6 |
| Native IsViewable only | 8 |
| Native VisibilityUnobscured only | 4 |
| Visibility plus direct-child geometry | 0 |

The assessor reports4 clear and8 UNKNOWN. This tests an explicitly stronger **parent-owned-region** contract. Ordinary screenshots legitimately include child pixels. Do not adopt this as a general screenshot refusal rule or infer input authority from the result.

Six cases twice: CLEAR, SIBLING_HALF, SIBLING_FULL, CHILD_HALF, CHILD_FULL, RESTORED. All24 capture attempts are retained:22 successful and2 original-method TypeErrors on fully sibling-covered source windows. All12 root-screen captures match independently reconstructed native rectangle/pixel evidence. Sibling-obscured target pixels are unspecified and never scored against imagined hidden content.

The initial expectation of24 successful captures was corrected after excluded construction and explicitly published BEFORE formal case0. The exact TypeError was prospectively allowed only for those2 source attempts. No capture was substituted or retried. Source and full final H/T/D/C/U were publicly committed at2295af8ab7d7dea577107a019d7ad52225864aee; freeze SHA25619a1f1931329b13868573b18c2544ad52da54b6fb766c729535a00fa57ef0145.

## Inspect without repeating an allocation

EVIDENCE.json binds seven base64 parts:32464-byte XZ archive,215 original source/raw/construction/exit/report files,402262 restored bytes. Every member is checked. The data-only helper refuses an existing destination and executes no study.

```sh
python -S -B unpack_evidence.py /tmp/capture-visibility-review-new
cd /tmp/capture-visibility-review-new
python -B audit.py formal
python -B controls.py formal
python -B -m unittest -v test_policy
```

Read restored REPORT.md, PLAN.md, CONSTRUCTION.md, the incident records and VERIFICATION.json. Do not rerun the consumed launch.py allocation. SOURCE.json and unpack_source.py independently preserve the exact twelve preformal source files. Directly readable policy.py and capture_slice.py match those frozen bytes.

Original audit:678 checks/errors0;13 effective evidence mutations rejected;10 unit methods pass. Actual audit/control/unit exits are retained. Fresh restoration reproduces the original audit and control output byte-for-byte, all215 member bytes, and5 packaging refusal controls. Separate implementation/process by the same author is not external human review. All36 recorded renderer/server/case-runner processes exited0 and were subsequently absent. Terminal keys/buttons/windows empty; sockets removed.

## Limits and integration meaning

Provided Linux6.18.44/x86_64 container, CPython3.13.5, Python-Xlib0.15, Xvfb2:21.1.16-1.3+deb13u1. No Docker/OrbStack image attestation, model/provider, host desktop, user data, input/XTEST emission, installation or experiment network. Timings are diagnostic, not performance. Current backend capture methods are preserved in a standalone measurement adapter; the full public runtime/admission/input path was not exercised.

Flat opaque same-depth rectangles and quiescent acquisition are assumptions, not general compositor/Shape/alpha/arbitrary-toolkit coverage. The concrete #40/#48/#2789 constraint is to distinguish image availability, returned content and parent-only visibility. No production mechanism/default, model benefit or global-roadmap completion is claimed. Repository-wide local tests were not run; PR CI is a separate delivery gate.

X.Org primary specification: https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html (XGetImage and VisibilityNotify). This is a measured support boundary, not a novel X11 theorem.
