# Office X11 Calc conformance v0 — finite plan

Stack: portable contract `0f2bda3...` -> retained private X11 backend `c96fe562...` -> this office policy/experiment.

One private Xvfb/Openbox/LibreOffice Calc instance opens a generated XLSX containing `A1=seed`, `A2=old`. The executor must not read workbook contents. It first verifies a stale observation refuses before backend input, then runs one accepted AST: EWMH focus, fixture-bound sheet click, Ctrl+Home, paced `office`, Enter, paced `preview`, Enter, Ctrl+S, bounded format-confirmation Enter, terminal release.

Only after the executor exits does a separate openpyxl scorer reopen the XLSX. PASS requires exact `A1=office`, `A2=preview`, `A3=None`, stale zero-input refusal, transport admission, and verified empty terminal release.

No model/provider/network, no shared display, no native Windows/macOS/Wayland claim, no broad office reliability claim. Result ID is one-shot after source freeze.
