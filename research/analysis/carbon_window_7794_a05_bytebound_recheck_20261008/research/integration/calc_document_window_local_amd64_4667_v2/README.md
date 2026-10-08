# Calc document-window local amd64 successor

This is a new construction-only successor to #4667. It preserves the original
STOP, which used an unavailable linux/arm64 image on another host. This package
uses only this PC's cached, immutable linux/amd64 image; it does not claim
cross-architecture equivalence.

`runner.py` creates a deterministic disposable XLSX with A1=0, launches a fresh
Xvfb and Calc process, sets live A1=7 without saving, records the root X11 tree
and an `xwininfo -id` receipt for every named child, then records an independent
stdlib ZIP/XML read and pre/post workbook hashes. `audit.py` is stdlib-only and
does not import the runner or use UNO. It independently reconciles every XID,
window title, map state, workbook value, and hash.

The exact run is frozen in `FREEZE.json` and Issue H/T/D/C/U. Inputs/source are
read-only; only a fresh output directory is writable. No user desktop, GUI
session, network, model, GPU, or Agent Interface runtime is touched. This is
one synthetic Calc presentation-state observation, not a formal #34 result.
