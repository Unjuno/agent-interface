# Authority-safe handoff capsule contract (successor v2)

This is a pure, advisory validator. It never transfers live authority, replays input, calls a model, or interacts with a GUI. A capsule is accepted only when session/task identity, bounded lifetime, explicit uncertainty, replay prohibition, and fresh-authority requirement are present. Stale, malformed, contradictory, or authority-bearing capsules are rejected.

H/T/D/C/U: Handoff metadata may aid recovery only as bounded context. T: finite negative/positive matrix in a pinned Python 3.12 container. D: 8 unit cases, network disabled. C: contract evidence only; accepted means advisory metadata, not authority or task correctness. U: live planner handoff, fresh acquisition, and two-domain recovery remain unverified.
