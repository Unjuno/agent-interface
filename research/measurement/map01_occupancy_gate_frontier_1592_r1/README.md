# MAP01 occupancy gate frontier

Successor analysis for Issue #1592. For nested interval refinement [L+dL, U-dU], the unchanged width/upper gate is equivalent to dL+(1-q)dU >= (U-L)-qU. The runner compares direct gate evaluation with the frontier on frozen boundary controls and 200,000 seeded valid refinements.

This is an analytical planning bound only. It does not measure live telemetry, authorize a recovery allocation, or claim physical/task efficacy.