# A03 construction failure

Disposition: FAIL_CONSTRUCTION_ASSERTION; no retry under A03.

The candidate exercised the hard-health schedule through monitor invalidation, planner interrupt, cover cancel, verified empty release, late planner answer, and rejected final admission. Its assertion expected one terminal receipt but the test fake and the literal V39 loop each appended the same receipt, so the harness observed two. The duplicate is in the test harness's record list; the production controller code was not changed. No candidate result JSON was produced and the independent audit did not run. Retained stderr SHA-256: ef5b75a5ef5048fabc864483959fbacd14b8a1bdcd0e1d0544e4076648894a7f.

A04 removes only the fake wait's duplicate local append; decision thresholds, source AST, schedules, and gates stay fixed. A04 has a distinct output path and freeze.
