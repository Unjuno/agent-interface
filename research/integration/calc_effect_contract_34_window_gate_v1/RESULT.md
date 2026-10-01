# Issue #4643 — construction outcome

Allocation: `calc-effect-contract-34-window-gate-20260927-01`  
Disposition: **`STOP_CONSTRUCTION`**  
Formal cases: **0**; construction runs: **1**; retries: **0**.

## Frozen environment and source identity

- Image: `issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`, linux/arm64; LibreOffice 7.4.7.2, Python 3.11.2, UNO, Xvfb.
- Network disabled, read-only container root/source, only disposable result mount writable; fresh profile and workbook.
- Source Git blob IDs: PLAN `45b448ccb6fc1bd107769fcc0ffbe19418afa270`, runner `32c50555d4c21fceef127c089612537c5a463876`, auditor `58b9c68783b1096c303931dd41790d46ff857502`. These match local `git hash-object` before execution.
- Container `py_compile` passed with `PYTHONPYCACHEPREFIX=/tmp/pycache`; the initial compile check without that setting hit the read-only source mount when Python tried to create `__pycache__`. No experiment case was consumed by that compile-only check.

## First outcome (preserved)

The runner completed the UNO edit and recorded live A1=7.0, initial A1=0.0, modified/unsaved=true, no save/store calls, independent disk A1=0, and unchanged source SHA-256 `82dcdfb3febafdc1cd78bac6a925ae5f33d38adf5b79f970f433cfba739b69bc`.

The same-run `xwininfo -root -tree` output contains a `VCL ImplGetDefaultWindow` at `0x20000b` and a separate top-level `baseline.xlsx - LibreOffice Calc` at `0x200325`. The queried VCL window attributes report `Map State: IsUnMapped`, so the frozen requirement for the VCL child to be `IsViewable` fails. The independent auditor exited 2 and emitted `STOP_CONSTRUCTION`, with sole error `same-run VCL window is not proven viewable`; it also independently reread the workbook and hash successfully. The other top-level window was not part of the frozen target rule and has no retained per-window attributes, so it is not used to override this result.

Raw SHA-256: `ee5fbd8fac9454d1c03110005761558beee325a6ef679fff74b1c2b62965ecca`.  
Audit SHA-256: `cdf8cf1a70af4a319230e7c66d85c0709ed9bf4d0126318da3b29f6be35432d9`.  
Baseline XLSX SHA-256: `82dcdfb3febafdc1cd78bac6a925ae5f33d38adf5b79f970f433cfba739b69bc` (4,815 bytes).

## Interpretation and limits

This improves evidence over #4626 by retaining same-run root-tree and window-attribute observations, but still does **not** meet the pre-registered window gate. The separate document-titled top-level window is a lead for a distinctly preregistered observer experiment, not grounds for post-hoc relabeling. No conclusion about Agent Interface runtime behavior, false completion rates, model-facing policy, modal tasks, or broad #34 promotion follows. Preserve this first outcome; do not rerun this allocation.
