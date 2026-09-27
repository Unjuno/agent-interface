# Optimistic read/write X11 transfer R1

Task `OPTIMISTIC-READWRITE-X11-TRANSFER-R1-20260919-001` / Issue #1750.

## H
The #1723 complete-read/write-set commit criterion transfers to two real X11 surfaces when currentness/effect state is represented by X11-owned generation/effect properties. Independent local resources admit PARALLEL. A cross A-write/B-read root-global dependency must SERIALIZE and make B reprepare after A changes the global generation. A surface-ID-only comparator intentionally admits the same unsafe pair and exposes stale G0. An exogenous B-local generation change must REVALIDATE before effect.

## T
Private Xvfb; two mapped Tk fixture processes with distinct XIDs and independent AF_UNIX effect-owner sockets; independent Python-Xlib observer. No XTEST/task-input. Formal schedule is three repetitions of all four scenario families, with cyclically rotated family order: 12 fresh cases total. One outer invocation. Independent audit does not import candidate code.

## D
PASS iff all12 cases complete/cleanup; INDEPENDENT3/3 PARALLEL with LOCAL1/LOCAL1; SHARED_GLOBAL_CANDIDATE3/3 SERIALIZE, old B receipt stale after A, exactly one reprepare, final GLOBAL=1/B=G1 and no stale G0 effect; SHARED_GLOBAL_SURFACE_ONLY3/3 unsafe overlap with A-before-B and final GLOBAL=1/B=G0; EXTERNAL_STALE3/3 REVALIDATE with B effect-command0 and final NONE; distinct mapped XIDs; independently recomputed decisions/resource/currentness agree; audit/corruption/source integrity pass; formal1/reruns0.

## C
AF_UNIX owner sockets are fixture commit boundaries; no shared keyboard/pointer routing or real application semantics. Complete dependency coverage is assumed; #508 remains the bypass-read warning. Wall-time speedup is not a gate.

## U
Private Linux/X11 fixture only. No model/token/human-tempo/cross-backend/production scheduler claim.
