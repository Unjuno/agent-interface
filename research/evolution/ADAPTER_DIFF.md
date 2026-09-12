# Adapter inventory against the shared runtime

Inspected reference: `interactive_v10.py` and its manifest at `7427bdd`.
Legacy transfer entrypoints inspected: `visual_tracking/async_events.py` and
`doom/session_v4.py`. This is a source inventory, not a validated port.

| Concern | Shared candidate | Legacy tracking / DOOM |
|---|---|---|
| Executor | executor_v3, absolute validity | Both import executor_v2; submit has no validity argument |
| Input ownership | dedicated input_owner_v2 connection | Both inherit session_v2 worker-owned input |
| Focus | capture samples and bound intent | Observation sequence only; no corresponding focus binding |
| Recovery | read-only observation without authority renewal | Different older execution semantics |
| Presentation | full default; explicit optional compact | First-per-step plus latest polling; tracking has pending signal map |
| Shutdown | close executor, input owner, app/session | Close executor and environment; no dedicated owner lifecycle |
| Domain operation | finite keys/text/hold and observations | Tracking adds track_red up to 30 seconds; DOOM uses ordinary key holds |

DOOM's existing real-time environment validation and asset hashes can be retained:
ASYNC_SPECTATOR, OS key input, cached-telemetry refresh outside the clock wait,
and outcome scoring after control. The adapter must update submit/deadline
handling and explicit owner lifetime, and pin the exact shared backend. Do not
silently keep the old backend while claiming common semantics. A basic-room
outcome still does not demonstrate general game skill.

Tracking requires more than changing imports. Its custom loop directly calls raw
input, has a thirty-second operation budget, and detects known visual signals in
an overridden snapshot method. It must bind authority before its custom branch,
respect lease cancellation and release, and define how the domain-specific
operation budget fits the shared contract. Its pending-signal/acknowledgement
logic cannot be discarded merely to simplify integration. This is a potential
subsystem-semantic change requiring separate evidence and a churn entry.

Priority: DOOM adapter first because its existing operations fit the shared input
vocabulary; track_red integration follows an explicit authority/event contract.
This prioritization reduces architecture uncertainty and cross-domain gaps.
No port is implemented or promoted by this note. Frozen legacy sources remain.
