# Calc: inspect the saved sheet before explicit finish

One primary-assistant WSL trial on source 8dda26f2c, seed 991124, six-stage bound,
2 ms text policy. The assistant entered A1=660 and A2=811 and saved. A partially
painted format dialog was returned. Stage 2 explicitly observed it through the
read-only window-review path, returning a painted dialog. Stage 3 clicked the
visible XLSX confirmation without finish_after. The next image still contained
the dialog, so stage 4 explicitly observed again. Sequence 11 showed the sheet
with the dialog absent and cells 660/811 visible. The primary assistant reviewed
that image, then issued stage 5 finish referencing sequence 11.

The saved workbook independently reads 660/811 with B1 empty. Evaluation and
cleanup completed. The final submit's process snapshot was still ready, so one
native_status query confirmed owner PID 20622 terminal, exit 0. Relay session
8101 exited 0 on EOF. Five delivered images, two input programs, two observation
requests and one explicit finish are retained. No input retry or corrective key
was issued; earlier feedback needs_review values remain unchanged.

This run establishes a usable explicit observation/finish path for this case.
Visual completion is the primary assistant's reading of retained sequence 11,
not a claim that the artifact auditor classifies pixels. It is separately backed
by the saved workbook check. Seven MCP calls were used (start, five submissions,
status); compared with the earlier finish_after trial this adds work to inspect
the UI. No speedup, lower cost or general reliability follows. The larger stage
bound and changed finishing policy prevent an identical-protocol comparison.

Run audit.py with Python/openpyxl to check retained hashes, exact images,
request/reply/continuation linkage, input-free observation stages, input releases,
saved cells and terminal state. The manifest covers all files except itself.
This is a same-assistant retained-evidence audit, not independent review or new
execution. No sensor or background watcher was built; Docker was not restarted
or used. Model tokens/cost, host presentation latency and human baseline remain
unmeasured. Earlier failures and incomplete visual feedback trials are preserved.
