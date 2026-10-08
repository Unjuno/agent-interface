# O3 multi-application negative matrix

Governing issue: #2811. This is an actual Docker/Xvfb experiment, not a documentation-only check.

## H/T/D/C/U

- H: the live evaluator rejects stale, partial, wrong-region, ambiguous, and forged-window observations while admitting only complete/current observations.
- T: launch two real GTK fixtures in fresh Docker with --network none; send Ctrl-S through Python Xlib/XTEST to each observed XID; evaluate six cases for each app using the same allocation.
- D: image agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, Xvfb :148, model calls 0, network calls 0. Observed XIDs: app_a=4194307, app_b=2097155.
- C: FAIL_O3_MULTI_APP_NEGATIVE_MATRIX. complete/current admitted on both; stale, partial, wrong-region, and ambiguous denied on both; forged source_window=9999999 admitted on both.
- U: this confirms the source-window identity defect across the multi-app path. The prior positive transport result remains valid only within its stated scope. A successor must bind source_window to a trusted observed XID before evaluator admission.

The experiment was performed against the existing GTK fixture and existing pure O3 evaluator. The failure is preserved unchanged and is actionable for #3131.
