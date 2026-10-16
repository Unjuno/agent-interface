# Frozen plan — Issue #956

- Current controller target gate pinned to Git blob `0e44f30660d4ef2b4a78ac2b92db7991e7d1c48a`.
- Exact gate: radius 5 (11x11), same-shape/in-bounds, max RGB-code error <= 8.0.
- Four fixed placements/background seeds.
- Per seed: stable identity, ID-only swap, changed-color negative.
- Inkscape 1.4, 640x480 export, same render command across arms.
- Independent XML oracle is audit-only and never enters `gate.py`.
- One deterministic formal invocation; reruns/replacements/tuning 0.
