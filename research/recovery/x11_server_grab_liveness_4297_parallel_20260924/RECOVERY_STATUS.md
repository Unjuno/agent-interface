# Parallel #4297 branch recovery — 2026-09-24

**Disposition: STOP_PARALLEL_DUPLICATE_BEFORE_FORMAL. No independent scientific result is established by this branch.**

This snapshot preserves the exact ten files present at the tip of `research/x11-server-grab-liveness-20260924` (`4112f8b4b6a4ba67acefb64d1a4d41d08278fe8f`). They are namespaced separately from the original owner's #4297 result because the branch reused the same integration path and would otherwise delete/replace files from the original branch when compared with current main.

Issue #4297 records that this worker's allocation-01 formal invocation stopped after three rows with `STOP_HARNESS_MARKER_RACE`; those rows were not pooled or reused. The later allocation-02 freeze was explicitly stopped after discovering the prior owner on `research/x11-server-grab-liveness-20260923`; allocation-02 formal invocations/rows/reruns/replacements were 0/0/0/0. Its construction results are excluded. Do not treat either freeze as the original owner's reported PASS or as a substitute for that owner's missing raw evidence.

The two committed source archives and their manifests are retained byte-for-byte for auditability. No Xvfb or formal experiment was rerun in this recovery. Issue #4297 remains open; no production or cross-platform claim follows.
