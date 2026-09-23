# Source-window binding gate fix

Issues: #3131, #2811

## H/T/D/C/U

- H: passing a trusted observed X11 window identity into the O3 evaluator prevents forged source-window evidence from being admitted.
- T: add an optional trusted_source_window parameter; reject mismatches; run the existing unit suite and the real two-GTK-app negative matrix in a fresh Docker container.
- D: agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, --network none, Xvfb :148, Python Xlib/XTEST, two real GTK fixtures, model/network calls 0.
- C: PASS_O3_MULTI_APP_NEGATIVE_MATRIX_SCOPED. Four unit tests passed. complete/current admitted on both apps; stale, partial, wrong-region, ambiguous, and forged XID denied. Forged cases now return source_window_mismatch.
- U: scope is source-window binding plus the existing six-case multi-app matrix. It does not establish arbitrary-window authenticity, model-level success, or broader GUI generality.

The pre-fix failure is preserved in the earlier merged result under #3151; this PR adds the fix and its post-fix Docker evidence.
