# r186 result: manually replaced private display and fresh game effect

The single predeclared WSLc run exited 0 and reported 18/18 gates true. The
old-target fixture logged exactly one delayed injection, and all 260 frozen
source file hashes still matched. A fresh ViZDoom target's measured coast was
0.0 map units and its 600 ms guarded W action produced 153.405 units of
displacement. XRecord captured the fresh W press/release, no B press before
the old delay horizon, and the injected B positive control afterward. The old
target exited before old Xvfb teardown; old task cleanup remained UNKNOWN and
replay was prohibited. The old cookie could not connect to the replacement
same-number display. `wslc list` showed no running container afterward.

The runner output includes `The config file ... could not be saved: No such
file or directory` during final game cleanup, after the temporary configuration
directory was removed. The run's exit status and measured gates were successful;
the warning is retained in `r186-output.txt` and is not counted as proof of
clean configuration persistence. The host also warned that swap limits were
unavailable.

Raw results and target/owner receipts are under `output/`; frozen conditions and
source/runner hashes are in `CONDITIONS.md`. This is one forced-order sample on
a synthetic fixture. Display replacement is manual, the fresh target is
DoomGame-managed rather than pidfd-owned, and no automatic isolation, old-task
success, reliability estimate, speed comparison, physical desktop or MAP01
completion is established. Old delayed-request flush does not prove the old
server accepted it. No model call was made.

An offline cross-check `python -B audit_raw.py` passed: it recomputed distances
from recorded positions, checked logged injection identity, event/horizon order,
receipts and source hashes. `raw-sha256.json` inventories 49 output files. The
injection log timestamp precedes the marker timestamp by about 0.33 ms; the
runner's horizon uses the later marker. This is a re-audit of retained values,
not an independent position sensor or an additional live sample.
