# C06 runner freeze

Frozen before candidate execution.
- Source-design commit: 8f13efb2597fc9c3fff0f68d73d37edbf9dcbc28
- Candidate SHA-256: d544618f50375b26b0415219e753ba96179916462fbbf2df4bad2f17c335c5df
- Independent auditor SHA-256: f95a859a6ed5be222a32670b78a5636ebb67dcb3d11a048785fb6cd6a80e64f0
- Runner SHA-256: 603b88ca89e46b0a2922c6da4b84302642bc7a5a24e9da37736608536bc50f7f
- Candidate stdout/raw must be committed as one additive ref update before invoking the auditor.
- Raw data uses six integer probability denominators encoded per the frozen plan; no action oracle is exposed in candidate input.
- Runtime target: local Node.js CPU process; no game, GUI, model, or shared WSLc/Docker runtime.
- This record is prospective; no candidate or auditor has run for C06 yet.
