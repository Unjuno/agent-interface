# A03 result

Disposition: **STOP (incomplete trace)**. The frozen `:118` focus smoke passed, then the candidate was invoked exactly once at `:117` and exited 2 after recording `TimeoutError('client event dispatch timeout')`. The raw trace has 40 admissions, 40 per-key releases, and 80 server keymap edges, but zero client events. The raw-only auditor ran once and returned `FAIL`; this does not override the preregistered STOP classification for an incomplete trace.

OrbStack guest `research-59-v39-xvfb-release-a03b-20261005` (ID `01M446MG7TSY1WSFFP44D3FK2R`) used Ubuntu 24.04.5 arm64, isolated=true, isolate_network=true, with only the frozen bundle and dedicated result directory mounted. Bundle SHA-256: `c8627962dc970231d3b8f3d36629f18cce6bb896691a54a769abcc8236c9bdf2`. The experiment freeze was based on main `8c45935e065ec36f8d42b7d4e59224900d5a83d2`; PR #7767 merged as `d799afce583e7a94ebd5df6b28ebeea9b1dce3f0` after that freeze and during this run, so A03 does not exercise that newly merged tree. Focus smoke used display `:118`, exact focus readback passed, and Xvfb exited 0. Candidate ran on `:117`; its raw cleanup confirms Xvfb stopped (exit 0). Guest is stopped and retained. A separate initially mis-mounted guest (`01M446HTBK1ZGX7D770WA5JWA2`) was stopped before any candidate invocation.

This is local Xvfb/InputOwner/client-event boundary evidence only. It is not the actual V39 game or model-authored policy, threat exposure, task effect, or MAP01 live attempt. It does not satisfy Issue #59's main evidence gate.

## Hashes

- `RAW.json`: `e8e133bda45604dbd3ad8c7757b7a15dbc97ab83ac61d60b02b6414d71876610`
- `AUDIT.json`: `8df3947f080346358bd96fc4c4109f5d34c72642cc4d72f317b512a723a7cb97`
- `setup.log`: `00b5b4a2c89468ba1083685a94955a3790ab9868c75e04c3178af2e1e0d9d35e`
- `focus-smoke.json`: `97d576ef4f4726ca6e7b9624390377346a6193d2346b566c4421bdd208995fce`
- `preflight.json`: `5ea938d275412808aa308ebfbc1fe3be995e62814cc74a834ca495991b7852b855`
- `candidate.exit`: `53c234e5e8472b6ac51c1ae1cab3fe06fad053beb8ebfd8977b010655bfdd3c3`
- `auditor.exit`: `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`
- `status.txt`: `db9741f8cc328034a0cb83d25729846a4902f30ac1ddf9b7343c35a3020576ac`
