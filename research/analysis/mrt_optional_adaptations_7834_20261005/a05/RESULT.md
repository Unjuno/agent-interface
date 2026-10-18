# A05 — FAIL_METHOD

Allocation MRT-7834-A05-20261005; freeze #5986630463; first result #5986643544. Candidate and auditor each ran once in separate WSLc 3.0.1.0 Node 22 containers, network disabled, pull never, CPU 1; both exit 0. No retries.

The frozen D gate expected M0=+2, M1=-1, pooled=+0.5, heterogeneity=+3. Candidate reported +1, -0.5, +0.25 and +1.5. Both candidate and auditor divided the probability-weighted sums by the two assignment support rows, halving the stratum effects. The auditor shared the same denominator defect and falsely reported agreement. Its mutation checker rejected only 6/7 because it ignored unknown extra keys.

The first result remains a formal FAIL_METHOD and is not rerun, edited, or promoted. A06 is a new allocation with fresh source identities and a corrected independently reconstructed oracle. This synthetic failure does not inform real users or product benefit.
