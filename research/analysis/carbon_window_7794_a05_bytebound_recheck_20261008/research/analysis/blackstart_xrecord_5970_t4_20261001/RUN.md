# T4 run record

## Construction and environment

- Docker Desktop backend processes exist, but the Linux engine service is stopped/manual and the configured named pipes have no server response. WSL2 `docker-desktop` distro is stopped. Service start is unavailable under current permissions. T4 therefore uses the private WSL2 `xvfb-run -a` fallback, not a container.
- Python-Xlib `record` and `XTEST` extensions import in WSL Ubuntu 24.04.4. A first private-Xvfb context smoke successfully created a context but errored when treating returned integer XID as an object; it dispatched no input. A corrected private-Xvfb smoke created, disabled, and freed a RECORD context successfully; no input dispatched. These STOP/construction outcomes are not candidate trials.
- Exact T3-derived fixture sources are hash-pinned to T3's merged source-archive transform. No new app/observer source derivation or upstream allocation retry is permitted.

- A no-input callback lifecycle smoke returned StartOfData and cleanly disabled/freed the context. A trial runner invocation against `/tmp/t4-probe` also dispatched no input and validated launch wiring.
- Candidate launch initially STOPped before X input because the sparse worktree omitted the T3 fixture path (4-level parent calculation); correction used the actual sparse checkout root and then the single frozen candidate invocation ran. Candidate was not rerun.
- Candidate raw X RECORD capture received two 32-byte FromServer payloads. The recording thread reported `TypeError("object of type 'NoneType' has no len()")` during disable/teardown; release and keymap checks completed. This teardown diagnostic is not hidden or treated as a missing-payload failure.
- Independent audit was accidentally started once using host Python (no Xlib) and STOPped before reading candidate data. The auditor then parsed under WSL. Its first parser constructions STOPped because EventField needs the low-level protocol display (`d.display`) and Xlib window resource objects are not integers; corrected parser read-only reran on the same unchanged raw bytes and passed. Auditor final output is the single retained `audit.raw.json`.

## Exact one-shot commands

The frozen candidate was invoked from the Windows host using `python research/analysis/blackstart_xrecord_5970_t4_20261001/candidate.py`; it verified the T4 source and T3 derived-source hashes, then ran one bounded Shift press/release under a fresh private WSL2 Xvfb with X RECORD active. It wrote `candidate.raw.json` and complete raw callback bytes under `run/`. The independent raw parser was invoked once successfully in WSL as `python3 research/analysis/blackstart_xrecord_5970_t4_20261001/audit.py`; it decoded the retained blocks and wrote `audit.raw.json`.

No #4135 formal allocation is rerun; raw result, cleanup release, and terminal keymap are preserved separately.
