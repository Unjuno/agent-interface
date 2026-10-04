# Run record

- Base: `3dbbda05eb8d5067ee2c2969615e472a0f20f562`; all source blobs were resolved from this commit and checked against `FREEZE.json`.
- Candidate v1 first stopped on a freeze key error; after the freeze schema was completed, it emitted `RESULT.json` with incorrect field lookups. That output is retained, not used for inference.
- Candidate v2 command: `python3 -B candidate.py` — exit 0; `HOLD_TOO_FEW_INDEPENDENT_RUNS`.
- Independent audit command: `python3 -B audit.py` — exit 0; independently rechecked 1,051 archive members and the stated decision gate.
- No runtime/container was used: this T1 test only parses pinned source evidence, and the archive was read in memory.
- This audit did not perform a live route/model/task experiment and did not access private/unpublished evidence.
