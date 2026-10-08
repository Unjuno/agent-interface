# XTerm prospective operation/target rows — first formal outcome

Decision: **READY_XTERM_OPERATION_TARGET_ROWS_SCOPED**. Formal1/reruns0.

The one frozen 64-row private-XTerm shadow collection completed with 64/64 rows validated under the exact #1132 contract, positives32 / semantic negatives32, TYPE_TEXT16 / SCROLL16, NO_LOCAL_ACTION16 / YIELD16, target-alternative rows8, split units16, window-evidence mismatches0, model/provider/task-input actions0, and four distinct lossless frame states. No proposed operation was executed.

The frozen auditor v1 passed the unmodified first result, but its frozen corruption suite rejected only7/8: changing a retained screenshot SHA to another syntactically valid 64-hex value was not bound to the actual PNG bytes. This failure is preserved. There was **no formal rerun**. A postformal independent auditor-v2 adds only the missing file-binding check and verifies all64 RESULT screenshot SHA values against the retained PNG files. Audit-v2 passes and postformal corruption controls reject8/8 including the exact previously-undetected frame mutation. RESULT SHA-256 remains `fcd05b5840c379bb03e4e4a261a648e39baa0bc423470ec345b524f2fa46d922`.

Postformal frozen scientific source/input comparison is exact. Auditor-v2 and controls-v2 are new postformal integrity code only; they do not alter row generation, renderer, oracle, thresholds or formal result.

Scope remains narrow: this proves prospective #1132 row-contract population on a controlled real XTerm renderer, not arbitrary-app perception or a learned-model benefit. Per #1591, the next rung must run the smallest deterministic structural rule over this exact frozen corpus before any learned backend is considered.
