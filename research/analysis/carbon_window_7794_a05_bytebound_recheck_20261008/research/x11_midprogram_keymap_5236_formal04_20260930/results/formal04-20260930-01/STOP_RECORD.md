# Formal allocation 04 — STOP

This is the immutable result of the one frozen invocation and its one independent audit for allocation `issue5236-formal04-20260930-01`. No rerun, row replacement, or source adjustment is allowed within this allocation.

- Frozen source commit: `1adabfcb05f0c1f647d096ca852689ce5a519cb5`; runner wrapper exit 0, no timeout.
- All three rows ran in a private mount namespace with tmpfs `/tmp/.X11-unix`; host socket metadata was unchanged. Xvfb naturally exited 0 for each row. Layout initial/final readbacks matched, and both remap actors ran inside their wait intervals with exit 0.
- All three backend dispatches report `completed` with operations 0–5 and verified empty release. However, `effect.json` was absent in every row and the fixture event logs were absent/empty. Thus the independent application effect did not corroborate the dispatch; no scientific outcome can be assigned.
- The independent auditor returned `STOP_PROVENANCE_OR_RUNNER`, citing the control row's absent expected effect and absent completed effects for both remap rows. It also rejected the wrapper command form because the frozen child bootstrap uses Python `-c`/`runpy` and the auditor only accepted a literal `--child` argv token. The input/effect gap alone is sufficient STOP.
- The five frozen corruption controls ran: omitted row, swapped directions, wrong expected bytes, and missing actor receipt all rejected as STOP; changed saved output classified as `FAIL_STALE_MAP_EFFECT`, not a clean outcome. `all_rejected` was true.
- Full raw/wrapper and audit/corruption reports are retained beside this record. No Xvfb, fixture, or actor process remains.

Classification: immutable `STOP_PROVENANCE_OR_RUNNER` (dispatch lacked independent fixture effects; auditor also needs to recognize the frozen bootstrap). Any diagnosis or corrected experiment must be a separately recorded successor allocation with a new output path and freeze.
