# #8406 T1 A12 — private-server preflight verified

A12 retains A11's symbolic placeholder-to-claim mapping. A11 stopped before inference because its private Ollama store had no model tag. This allocation first verifies that the private server's API tag, digest-addressed blob, and manifest agree, using the store-specific server and an explicit `OLLAMA_HOST` for pulls. Only after that gate does it run the same 390-call paired schedule evaluation with fresh seeds. See `PROTOCOL.md` and `FREEZE.json`.
