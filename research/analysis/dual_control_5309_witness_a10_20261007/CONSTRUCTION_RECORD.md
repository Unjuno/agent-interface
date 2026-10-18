# A10 construction record

Before formal freeze, the initial test expected 72 cases. Executing the construction suite showed 132 actual cases because the three graph families contain 3+4+4=11 states and the frozen matrix crosses each state with 2 prediction states × 3 preservation costs × 2 prior-witness conditions. This was a construction-count defect, not a candidate/auditor run; candidate, environment, and auditor formal invocations were all zero at that point.

The expected case/arm counts were corrected prospectively to 132/264; the independent topology-signature assertion and all three construction tests then passed. The corrected source and input were hashed into `FREEZE.md`. No original A03/A08/A09 artifact was changed.
