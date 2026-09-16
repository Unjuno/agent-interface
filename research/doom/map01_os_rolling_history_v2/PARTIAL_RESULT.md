# MAP01 OS rolling history v2 — retained partial failure

**Decision: `ABORT_HARNESS_TEMPORAL_BINDING_CONTRACT`.**

Five of sixteen frozen cases completed. The continuous rolling-capture mechanism itself stayed within the 500 ms freshness gate and all completed controller releases verified empty. However, the frozen `choose_pair` rule selected the nearest available pair without an admissible temporal window. In case 4 it selected a **35.873 ms** pair for the opening condition although the unchanged history classifier was calibrated on a 2-tic effect interval (~57 ms). That case then misclassified opening as closing.

Because the successor was intended to change only acquisition architecture, allowing the effective history horizon to drift is a harness/scientific-contract defect. The allocation is stopped and is not completed, pooled, retried or interpreted as a rolling-history efficacy result.

Next version changes one thing only: bind a decision to an already-retained frame pair whose timestamp gap lies inside a preregistered state-independent admissible interval; if no pair qualifies, yield with zero task input. It also retains the rolling timestamp ledger. Formal seeds must be disjoint.
