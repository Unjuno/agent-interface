# R05 — contract-valid program identifier

R04 was stopped by static validation before runtime admission because its program_id was 73 characters against the 64-character contract limit. R04 sent no input and remains immutable. R05 changes only the program identifier to the frozen short value `calc-r05-314plus728` and receives a new attempt ID.

A read-only setup screenshot is saved as `pre-run-sky-observation.jpg` (SHA-256 `1b83ff6e269eee8c6fb68cf8a1e59f81cbcb0a21b1d65a698bf44604128e932f`); it shows Calculator Standard mode at 1,042 and is not the formal public-MCP pre-action observation. The user-authorized task begins from that state, clears it, then enters 314 + 728. It uses one public physical-screen pre-observation, one validation, one dispatch, up to five read-only exact-call result polls, and one same-session post-observation only after completed action and verified neutral release. The wall-clock limit is 90 seconds; no replay or recovery is allowed.
