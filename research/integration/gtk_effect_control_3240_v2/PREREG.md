# Additive auditor-schema reconciliation for Issue #3240

## H / T / D / C / U

**H** — The retained #3240 adapter receipt reports native completion at
`raw_dispatch.result.status`; an independent auditor that checks the nonexistent
`raw_dispatch.result.execution.status` will falsely report incomplete native
execution. Correctly following the raw schema should remove only that false
finding and must preserve the HOLD caused by the changing untouched-target XWD.

**T** — On current main `564351121726f25b67dcde0089bf26ccb15cd91e`, inspect the
immutable `gtk_effect_control_3240_v1/evidence/formal01` bundle and run the
standard-library-only `audit_raw.py` in a separate read-only OrbStack container
from image `sha256:296d358f5c71e6c3e766c49ebfe13b9b1ec5c2837157da2cfe406ee73bfb2992`
(`linux/arm64`). Do not rerun or modify the original allocation. Exercise the
auditor against the retained original and corruption controls for native status,
target image hash, and untouched-target stability.

**D** — PASS for this narrow audit-reconciliation hypothesis only if the
corrected auditor recognizes `raw_dispatch.result.status=completed`, keeps
`status=partial` and `task_success=null` separate from native completion, and
continues to HOLD on `untouched_target_pixels_changed`. Corruption controls
must be rejected. This cannot change the original allocation's HOLD result.

**C** — No GUI input, model/provider call, network, or new allocation. The
historical raw bundle is read-only; output is written to container `/tmp`.
Source changes are additive under `gtk_effect_control_3240_v2/`.

**U** — This verifies only one auditor field-path correction against one
historical two-row GTK/X11 diagnostic. It does not complete #3240, rerun any
GUI case, resolve why the untouched target's XWD changed, satisfy #2606's
eight-case acceptance, or establish application task success.
