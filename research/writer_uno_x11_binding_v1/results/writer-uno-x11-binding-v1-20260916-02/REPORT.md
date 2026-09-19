# Writer UNO/X11 document binding v1 — retained successor result

**Result ID:** `writer-uno-x11-binding-v1-20260916-02`  
**Source/plan freeze:** `57b3e54e03a6dd1e7640eb22813f4122182ce4cc`  
**Prior result:** `writer-uno-x11-binding-v1-20260916-01` — retained incomplete wrapper outcome, never rerun.

## Disposition

**PASS_REAL_WRITER_DOCUMENT_XID_BINDING / REJECT_POSITIONAL_ENUMERATION_IDENTITY / HOLD_PRODUCT_PROMOTION**.

Five paired blocks used fresh private Xvfb/Openbox/LibreOffice Writer sessions. Fixed launch order was A then B. In every positional arm, UNO enumerated B,A while X11 client list enumerated A,B; positional zip therefore targeted B. In every activated arm, the exact UNO document (`RuntimeUID` + URL) was activated A→B→A and `_NET_ACTIVE_WINDOW == input focus` converged to a repeatable A XID distinct from B.

| policy | sessions | target A exact | wrong-target effect | release empty |
|---|---:|---:|---:|---:|
| positional | 5 | 0/5 | 5/5 | 5/5 |
| activated binding | 5 | 5/5 | 0/5 | 5/5 |

The same XTest suffix `keeperoffice` at 12 ms/character was used. Positional outcome was A=`book`, B=`sidecarkeeperoffice`. Activated outcome was A=`bookkeeperoffice`, B=`sidecar`. Post-input text was read by a separate `/usr/bin/python3` UNO process.

## Retained harness failure

Result `-01` completed 9 of 10 planned sessions (5 positional wrong-target, 4 activated exact), then the outer 180-second execution envelope expired before the tenth session and before aggregate creation. It is incomplete, not PASS, and was never rerun. Successor `-02` reused zero `-01` sessions; only invocation was checkpointed arm-by-arm.

## Limits

This proves a scoped Writer/X11 binding mechanism in private Xvfb/Openbox. UNO Frame activation is an application-side control mechanism, not a generic OS window identity API. Titles are corroborating evidence only; the candidate relies on exact UNO URL/RuntimeUID plus activation and active/focus XID convergence. No Wayland, Windows/macOS, Unicode/IME, model/token or broad Office reliability claim.
