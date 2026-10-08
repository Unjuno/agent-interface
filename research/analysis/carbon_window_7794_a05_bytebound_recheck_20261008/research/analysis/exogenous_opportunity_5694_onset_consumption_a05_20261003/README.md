# A05 — candidate-consumed onset phase

This additive successor tests the measurement contract that PR #6805 did not: does the candidate read cue onset and compare it to actual capture timestamps?

The matched c01/c02 fixture arms share every field except onset (9 ms vs 11 ms); captures are at 10 and 50 ms, expiry is 20 ms, horizon is 60 ms. There are no precomputed capture-membership IDs or result labels. Candidate output must report the actual first capture inside the cue interval, or null.

Formal scope is a finite, authored synthetic timing method test using WSLc CPU. It is not live GUI or runtime timing evidence.
