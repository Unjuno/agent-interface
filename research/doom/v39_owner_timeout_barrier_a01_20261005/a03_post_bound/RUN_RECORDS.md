# A03 execution and audit commands

All commands were run on native Windows with Python 3.11.9 unless a specific failure is recorded. No X11, game, model, or live allocation was used.

| Run ID / purpose | Command | Exit / disposition |
|---|---|---|
| A03 v1 construction attempt | `py -3.11 probe_a03.py` | Exit 1 at helper import; neither arm started. Full traceback: `TOOL_STDOUT_A03_CAPTURE.txt`. |
| A03 v2 schedule attempt | `py -3.11 probe_a03_v2.py` | Exit 0, but immediate gate-open remained; protocol deviation retained, not a valid A03 pair. Full stdout: `TOOL_STDOUT_A03_V2_CAPTURE.txt`. |
| A03 v3 candidate schedule | `py -3.11 -m py_compile probe_a03_v3.py`; `py -3.11 probe_a03_v3.py` | Both exit 0. Candidate used the delayed gate; original baseline finalizer opened early, so its baseline is not used for the final comparison. Complete stdout: `TOOL_STDOUT_A03_V3_CAPTURE.txt`. |
| Control supplement v1/v2 | No experiment command issued | Frozen versions failed pre-run construction checks and remain unexecuted. See the two `CONSTRUCTION-A03-CONTROL-V*.md` files. |
| A03 control supplement v3 | `py -3.11 -m py_compile probe_a03_control_supplement_v3.py`; `py -3.11 probe_a03_control_supplement_v3.py` | Both exit 0. Executes delayed baseline only and reuses the saved v3 candidate JSON. Complete paired-output capture: `TOOL_STDOUT_A03_CONTROL_V3_CAPTURE.txt`. |
| Independent A03 audit | `py -3.11 audit_a03_control.py` | Exit 0; output retained in `AUDIT_A03_CONTROL.txt`. No arm was rerun. |
| Earlier evidence regression | `py -3.11 audit_result.py`; `py -3.11 audit_a02_v3.py` | Both exit 0 on the final package manifest. A02's incomplete stdout remains explicitly disclosed. |
| Package inventory | `py -3.11 write_manifest.py` | Exit 0; 68 files covered, excluding interpreter caches and the manifest itself. |
| Diff whitespace check | `git diff --check` | Exit 0. |
