# NativeHandleBridge explicit-review successor — PASS (bounded)

Issue: #3467; successor to STOP allocation #3464, not a rerun.

## H/T/D/C/U

- **H:** Explicit `review_window` should revoke p1 aliases and reject them before input, while a freshly minted p2 alias remains usable.
- **T:** One Obstac/OrbStack container allocation, network disabled; source `f33695096b7460dc148d348d6c9a26c7815c1569`; image `agent-interface-2558-orbstack:20260920`, digest `sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398` (linux/arm64). Same private Xvfb; p1 and p2 were distinct processes, with different XIDs (4194318 and 8388622).
- **D:** p1 PID/start ticks `14/3985427`; p2 `17/3985494`. Review status was `reviewed`; binding revision advanced 0→1 and scope changed. Exact patch SHA-256 matched across p1/p2: `700f2b981adf4167449d3eb71eb0b57c841939b11731c660112ee39b8bd08d44`. After review, alias A returned `refused` / `MISSING` (`unknown_session_alias`); backend emission counter remained 0→0 and p2 effect was absent. The separate XTEST wrapper recorded three events total, all after the fresh positive-control dispatch began. Fresh alias B completed, with counter 0→3; the three wrapped XTEST events were pointer motion, button press, and release. p2 wrote `{"pid":17,"effect":"clicked"}` and changed its title to `NR3467-EFFECT-TARGET`.
- **C:** **PASS_REVIEW_REVOKES_PREDECESSOR_ALIAS** for this exact path/allocation. Independent audit recomputed 16 gates from raw JSONL, XTEST event JSONL, and the p2 effect file. Raw JSONL: 5072 bytes, SHA-256 `c506bc3712acd200bee1cfc3ae10468af7de8fd115831ae78cae14c099de366c`; XTEST events SHA-256 `d856bc79545cb6ca935aea90089584cd3fcf79fa66f7d1f722b40965a3f25f58`; p2 effect SHA-256 `ec588cbaad031c6d9a6816933d307f32bef597207e7c4222ed2acb4b1b653648`.
- **U:** This validates only explicit review revocation in the pinned experimental NativeHandleBridge under this fixture. It does not test XID reuse (p2 used a different XID), implicit replacement detection, default runtime, broad GUI compatibility, human-tempo use, or release readiness. #3419 and the roadmap remain open.

Reproducibility files: `raw.jsonl`, `xtest-emissions.jsonl`, `p2-effect.json`, `audit.json`, and `audit.py`. No production source was changed.
