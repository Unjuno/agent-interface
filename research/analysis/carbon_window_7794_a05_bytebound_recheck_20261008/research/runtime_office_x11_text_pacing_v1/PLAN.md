# Office X11 text pacing v1 — frozen finite comparison

Dependency stack: portable contract `0f2bda3...` -> private X11 backend `c96fe562...` -> real Calc integration `4e16d8a...` -> this experiment.

Question: the retained real Calc integration used 12 ms per strict-ASCII character after unpaced `office -> ofice`. Test the fixed candidate delays **0, 1, 2, 4, 8, 12 ms** without changing semantic AST meaning.

Formal arm order is fixed: **0, 12, 2, 8, 1, 4 ms**. Each arm gets a fresh private Xvfb/Openbox/LibreOffice Calc session, fresh generated XLSX, the same 16-string repeated-character corpus, the same sheet acquisition/save policy, stale-observation zero-input control, and terminal release verification. Workbook contents are scored only after executor completion by a separate openpyxl process.

Each formal arm is one-shot. An outer display-wrapper `TERM environment variable not set` is not itself a rerun trigger when internal executor/scorer receipts are complete; missing internal evidence makes that arm incomplete. Aggregate PASS requires all six arms complete. The selected delay is the **minimum tested eligible** delay, not an interpolated threshold.

No model/provider/network, no shared display, no runtime mutation, no native Windows/macOS/Wayland claim, no general office reliability claim. Timing is local diagnostic evidence only.
