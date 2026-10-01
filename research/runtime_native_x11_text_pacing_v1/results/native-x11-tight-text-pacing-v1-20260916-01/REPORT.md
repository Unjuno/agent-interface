# Native X11 tight-loop text pacing v1 — retained first result

**Result ID:** `native-x11-tight-text-pacing-v1-20260916-01`  
**Source/plan freeze:** `48030f5829690bdd3209d05974e390d88e7742a9`  
**Frozen native-X11 source dependency:** `ca141254c949f7ce42f9967f752a517ff521421b`  
**Compiled semantic-core dependency:** `39a0ccc2a2cb401699d6ff8c8098d5a239caeaad`

## Disposition

**TRANSFER_PASS_NATIVE_TIGHT_1MS / RETAIN_IMPLEMENTATION_TRANSFER / DO_NOT_GENERALIZE**.

The source-frozen compiled Go+cgo/X11/XTest tight-loop candidate completed the fixed formal order `0,12,1 ms` once per arm on fresh private Xvfb/Openbox/LibreOffice Calc sessions with separate post-execution XLSX scoring.

| requested pacing | exact XLSX corpus | eligible | median native char-start interval | edit interval |
| ---: | ---: | :---: | ---: | ---: |
| 0 ms | 0/16 | NO | 0.0665 ms | 43.651 ms |
| 12 ms | 16/16 | YES | 12.353 ms | 1820.812 ms |
| 1 ms | 16/16 | YES | 1.204 ms | 204.491 ms |

0 ms preserved transport, stale refusal, and terminal release, but every scored string was semantically wrong (`office→ofice`, `coffee→cofe`, `committee→comite`, etc.). 1 ms and 12 ms both produced exact durable workbook semantics.

On this fixed native tight-loop Calc workload, 1 ms is **1.616321311 s / 88.77% shorter** than 12 ms at equal correctness. This is a local execution-interval comparison, not a product latency claim.

## Why this is stronger than the rejected development adapter

A first development adapter lowered each character through a separate backend `Execute` call. Its natural admission/release/XSync overhead created ~19 ms character spacing even when requested pacing was 0 ms, so it could not test the pacing hypothesis. That design was rejected before source freeze and no formal result ID was consumed.

The retained candidate instead injects strict lowercase ASCII inside one compiled native `Execute` loop. Formal measured char-start intervals (0.0665/12.353/1.204 ms) show that requested pacing is actually discriminated.

## Controls and evidence

- source readback matched frozen GitHub blobs before formal execution; source remained byte-identical afterward;
- frozen controller binary SHA-256: `bcd7b50ab3a96343b2f13044622aaf28d1909fa4a71fd2223f049d1b1d75b86f`;
- all arms refused stale text as `STALE_OBSERVATION` with zero injected events;
- all arms ended with verified empty release;
- 0 ms controller exit 0 / scorer exit 1 (retained semantic negative); 12/1 ms controller and scorer exit 0;
- all three XLSX archives pass ZIP CRC readback (11 members each);
- matrix/aggregate exit 0; formal arm reruns 0; model/provider/network calls 0.

The existing frozen `research/runtime_native_x11_v0/**` namespace was never modified. It remains capability-honest with generic `input.text` unsupported; this experiment is an isolated strict-lowercase-ASCII fork/candidate, not a silent capability promotion.

## H/T/D/C/U

**H:** the 1 ms text-pacing candidate transfers from Python/Xlib real-Office evidence to a compiled Go+cgo/XTest tight-loop implementation while 0 ms remains semantically unsafe.  
**T:** fixed source, fixed order `0,12,1`, fresh private Calc/XLSX per arm, independent scorer, measured native inter-character timing, stale/release gates.  
**D:** PASS because 1 ms and 12 ms are exact durable semantics, all controls pass, and 0 ms is retained as a meaningful negative.  
**C:** another X server/compositor, real WSLg, CPU scheduling, non-ASCII text, IME, or another native backend may shift the safe pacing floor.  
**U:** one host/container, Xvfb/Openbox, strict lowercase ASCII, one session per arm, no Wayland/Windows/macOS/model/token evidence.

## Successor

The next high-information test is environment transfer, not another same-Xvfb implementation: reproduce 1 ms vs 12 ms on WSLg/a real X display if available, or on a different compositor/backend. If 1 ms fails there, retain pacing as environment/backend policy rather than a universal default.
