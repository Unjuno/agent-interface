# LibreOffice Writer X11 pacing transfer v1 — retained first result

**Result ID:** `office-writer-x11-pacing-v1-20260916-01`  
**Source/plan freeze:** `cf3fff175622e3132e947f0ecb5b384a698961b2`

## Disposition

**TRANSFER_PASS / RETAIN_CROSS_APP_1MS_CANDIDATE / DO_NOT_GENERALIZE**.

The fixed formal order `0, 12, 1 ms` completed once per arm on fresh private Xvfb/Openbox/LibreOffice Writer sessions with native ODT output and an independent post-execution ODT scorer.

| pacing | exact corpus | eligible | task elapsed |
| ---: | ---: | :---: | ---: |
| 0 ms | 1/16 | NO | 1035.406 ms |
| 12 ms | 16/16 | YES | 2912.666 ms |
| 1 ms | 16/16 | YES | 1191.346 ms |

0 ms preserved transport/release but produced 15 semantic mismatches. 1 ms and 12 ms both produced exact durable Writer text. On this fixed Writer workload, 1 ms is 1721.319 ms / 59.10% shorter than 12 ms at equal correctness.

## Cross-application interpretation

The previous Calc pacing result independently found the same qualitative boundary: 0 ms failed repeated-character semantics, while 1 ms and 12 ms were exact. Writer therefore **transfers** the 1 ms candidate to a second real Office application under this private X11 setup. This does not prove a universal pacing constant.

## Controls

- source readback: 7/7 local source files matched GitHub blobs before first formal arm;
- formal arm reruns: 0;
- stale observation: `STALE_OBSERVATION`, emissions `0 -> 0` in all arms;
- terminal release: verified empty in all arms;
- executor exit code: 0 in all arms;
- scorer exit code: 1 only for the intentionally retained semantically wrong 0 ms arm;
- the Writer executor does not import the ODT scorer;
- no model/provider/network calls.

A fixed leading `sentinel` paragraph absorbs Writer's first-word AutoCorrect and is excluded from the scored corpus. This was established during development before source freeze; it is not post-formal tuning.

## H/T/D/C/U

**H:** the 1 ms candidate from Calc transfers to a second real Office app, while 0 ms remains unsafe under repeated-character XTEST input.  
**T:** source-frozen three-arm real Writer transfer, fresh native ODT per arm, independent post-execution ODT ZIP/XML scorer, fixed order `0,12,1`.  
**D:** TRANSFER_PASS because 1 ms and 12 ms are exact, 0 ms is semantically wrong, and stale/release gates pass for all arms.  
**C:** the requirement may still depend on Xvfb/Openbox, CPU scheduling, XTEST, application, locale, input method, or text distribution.  
**U:** one Writer session per arm, one host/container, strict ASCII, no Unicode/IME, no real WSLg/Wayland/Windows/macOS/native backend/model/token evidence.

## Successor

The next useful discriminator is **environment transfer**, not a third same-host Office app: reproduce 1 ms vs 12 ms on a real/alternate Linux display or the compiled native-X11 backend. If 1 ms fails there, pacing is backend/environment policy rather than a common semantic default.
