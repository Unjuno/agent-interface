# Frozen exact-crop cache memory-bound protocol (pre-formal)

This directory contains the immutable formal runner/auditor sources and a non-formal construction diagnostic. Formal Docker invocations remain **0** until Issue #5085 grants the exact allocation and the pinned image/current-main/source readbacks pass.

## Candidate protocol

- Run one fresh CPU-only, network-disabled container for `study_formal.py formal_raw.json` against the `FORMAL` profile in `FREEZE.json` (64 unique 800×600 RGB inputs, then revisit versions 56–63; LRU capacity 8).
- Only on runner exit 0, run the independent `audit_formal.py formal_raw.json formal_audit.json` in a separate fresh container. Inputs read-only, output directory fresh and writable; no retry, replacement, tuning, GUI, model, GPU, or input dispatch.
- Formal pass is `PASS_CACHE_MEMORY_BOUND_SCOPED`; a local reduced profile can only report `PASS_CONSTRUCTION_SCOPED`.

## Construction-only replay

```powershell
python -B study_formal.py construction_v2.json --construction
python -B audit_formal.py construction_v2.json audit_v2.json --construction
```

Observed host result: 12/12 score records equal, bounded 28,800 RGB-pixel bytes vs 144,000 unbounded, independent audit 96 checks, zero errors, and 5/5 corruption controls rejected. This does not exercise the 64-frame profile or Docker and is not formal evidence.

## Current stop

No exact shared-lane assignment is published for allocation `exact-crop-cache-memory-bound-4083-20260928-01`. Queue request is recorded at https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5868011186. The formal container image digest and runtime version readback are intentionally null in `FREEZE.json`; do not launch until assigned and frozen.
