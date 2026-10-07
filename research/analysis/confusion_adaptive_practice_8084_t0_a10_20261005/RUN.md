# A10 run record

- Base main: `f75ad203f41126c2382175aed398639796fe6d0d`; freeze commit `d7dfa634f064c86580e00d08ff188ae5cececba6` (rebased without changing frozen tree).
- CPython 3.12.10 exact interpreter path in FREEZE.json.
- Construction: 5/5 normal and 5/5 under `-O`; sparse-aware freeze stage/commit successful; freeze blob present in HEAD and package clean before generator.
- Generator: one invocation, exit 0, ~8.06 s; 160,000 rows.
- Candidate: one invocation, exit 0, ~1.64 s; input directory contained only candidate.py and observed_counts.json.
- Auditor: one invocation, exit 0, ~66.63 s; auditor-only SCORING.json stayed outside candidate input; independent reconstruction zero errors; all five mutation controls rejected.
- Only fixed-rate reference arm qualified one gate (.40/.80); no finite beta concentration arm qualified.
- Frozen source hashes verified; complete package checksum manifest retained.
- No container, WSLc, Docker, network, GPU, GUI, model, participant, or external data.
