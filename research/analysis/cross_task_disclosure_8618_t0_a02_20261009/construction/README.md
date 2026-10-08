# A02 construction record

A02 repairs only the A01 formal-runner preflight defect: frozen hash entries are package-relative and are now resolved against this allocation's package root. Candidate logic, policy cases, oracle truth, decision thresholds, and network-deny profile are unchanged. A02 uses its own `input/`, `src/`, `construction/`, `raw/`, and `audit/` paths.

Before formal freeze, the no-network construction candidate emitted 14 rows, the separate auditor reported `PASS_METHOD_SCOPED` with zero errors, and all four source/recipient/dependency/payload mutation controls failed closed to the certified general action. This directory is separate from A01's preserved candidate-construction outputs and its pre-candidate formal-runner STOP.
