# Issue #5692 A02 — visual pixels versus X11 input recipient

Allocation: `ui-redress-5692-x11-a02-20261001-01` (separate successor allocation; A01's terminal STOP is retained unchanged).

Prerecorded on GitHub Issue #5692 comment #5923744615 before A02 source repair/formal run. Base-main observation at preregistration: `a7648fb47f16b15ac2fdb63075186aad1189859c`.

## Root-cause correction

The A01 candidate attempted to read `ev.event`. Python-Xlib's `KeyButtonPointer` event schema contains a `window` field, and no `event` field. Source inspection plus a separate throwaway private-Xvfb event probe confirmed this for both ButtonPress and ButtonRelease. A02 adds only a normalization helper using `ev.window.id`; A01 source and freeze remain untouched. Regression test was run before repair and failed because the helper was absent; after repair it passes.

## H / T / D / C / U

- **H:** A mapped X11 InputOnly window with a full input shape can receive an ordinary pointer click while leaving the target crop byte-identical. Screenshot-plus-geometry admission cannot distinguish it, but an XQueryPointer child check can refuse it. An empty input shape is a negative control. Mapping the overlay after the check demonstrates a check/use race; XTest offers no recipient-bound atomic click.
- **T:** In one private Xvfb server, run fresh Tk target and separate overlay processes for CLEAR, visible InputOutput overlay, transparent InputOnly overlay, and empty-input-shape InputOnly overlay. For each condition compare `SCREENSHOT_GEOMETRY` and `RECIPIENT_PRECHECK`; add one forced diagnostic click for visible-overlay delivery and one barrier-directed post-check insertion. Each row stores exact target crop pixels before/after, SHA-256, process/window identities, pointer child, admission, and independent target/overlay press+release logs. Ten fixed rows total; no RNG or retries.
- **D:** `METHOD_PASS_SCOPED` only if: visible overlay changes crop and receives the diagnostic click; transparent InputOnly receives while crop is unchanged; screenshot policy admits that unchanged image but the recipient check refuses; empty input shape is not treated as intercepting and the target receives; the after-check overlay receives despite the earlier target precheck; all 10 rows replay and hashes validate. If the frozen overlay cannot be realized or event delivery differs, retain FAIL/STOP as observed; never patch/retry this allocation.
- **C:** Ubuntu WSL2, CPython 3.12.3, Tk 8.6, Python-Xlib, Xvfb private display, XTest. No Docker because Docker Desktop's `desktop-linux` read-only `docker ps` is still pending and the shared container queue has unresolved owners. This uses no shared Docker container and never connects to the user display.
- **U:** One Xvfb server and authored test windows only. No compositor behavior, real applications, hostile code, model, web content, user data, exploit prevalence, other OS/backend, current Agent Interface runtime integration, or production-security claim. XQueryPointer is a non-atomic precheck; the race row is expected to show that it cannot guarantee the later recipient.

## Frozen run

Construction only before freeze: 10/10 standard-library tests (9 auditor mutation/control tests plus the recipient-field regression), `py_compile`, and an isolated Xvfb Shape extension smoke probe (InputOnly window; empty ShapeInput query returned 0 rectangles). These are not formal result evidence.

Formal candidate command, exactly once:

```sh
xvfb-run -a python3 -B candidate.py --out raw.json
```

Independent audit, separate process and only if candidate exits 0:

```sh
python3 -B independent_audit.py raw.json --out audit.json
```

No candidate/auditor code is imported by the other. No network, model, GUI outside private Xvfb, web content, secret, or user desktop is used. Any candidate/audit failure is terminal for this allocation.
