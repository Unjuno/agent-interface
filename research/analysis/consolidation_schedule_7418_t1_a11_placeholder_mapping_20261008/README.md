# #8406 T1 A11 placeholder-mapping evaluation

A11 is a fresh model-evaluation allocation after A10 failed its frozen transition audit. The only intended design change is a symbolic placeholder mapping that explicitly distinguishes input slot names from their values and shows allowed output shapes. It retains the same fixture, schedules, query set, model family/digest, decoding, budget, and audit contract, with fresh seeds. See `PROTOCOL.md` and `FREEZE.json`.
