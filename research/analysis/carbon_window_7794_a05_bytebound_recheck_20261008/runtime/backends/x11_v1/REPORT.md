# Runtime X11 backend v1 integration

Task: `RUNTIME-X11-V1-INTEGRATION-20260917-001`, Issue #586.  
Integration base: `5cae8e6c210cf6b2ca5d4822d6d34cd56177c72d` (promoted `runtime/core_v1`).

Decision: **PASS_PRIVATE_X11_RUNTIME_INTEGRATION_CANDIDATE**.

## What is integrated

`X11RuntimeSession` now composes the promoted runtime core admission contract with
an Xlib/XTEST backend. Core freshness/lease/capability admission runs before any
backend input. A second pure X11 preflight validates native constraints before the
first XTEST emission. Only after both gates pass may execution begin.

The backend provides the office-floor capabilities on a private X11 display:
capture, keyboard, strict-ASCII text, pointer, scroll, focus, display geometry,
monotonic clock, feedback/wait and verified release-all. Targets are explicit
registered X11 window ids; supported coordinate frames are screen physical pixels
and window-client coordinates.

## Clean-copy integration result

One private Xvfb + Tk fixture block completed with **6/6 tests PASS**:

1. manifest is core-v1 ready while declaring the narrow text subset;
2. valid program performs focus + pointer + text `office` + Ctrl+S + capture + release;
   the independent Tk app writes exact effect `{saved:true,text:"office"}`;
3. stale observation produces zero backend emissions/effect;
4. stale binding produces zero backend emissions/effect;
5. expired lease produces zero backend emissions/effect;
6. backend-specific invalid text `ok!` returns typed `BACKEND_CONSTRAINT` before
   the first physical emission and ends verified empty.

The valid case retains one capture receipt and a verified final release with
`keys_down=[]` and `buttons_down=[]`.

## Construction failures retained

The integration was not treated as successful until these were resolved:

- inherited `XAUTHORITY=/opt/xvfb/.Xauthority` was absent in the disposable
  container, so the first setup stopped before any scored case. The test harness
  now uses private `Xvfb -ac` plus a private empty XAUTHORITY file;
- the initial Tk Ctrl+S scorer was bound only to the toplevel and did not fire
  after the Entry received focus. The independent fixture was repaired with a
  global binding; backend semantics were unchanged;
- most importantly, the first X11 text path validated characters while emitting
  them, so `ok!` could emit the accepted prefix `ok` before rejecting `!`.
  The backend now preflights the **entire program** before the first emission,
  including all text, focus targets and key mappings. This is the fail-closed
  boundary retained by the final zero-emission negative test;
- after the native preflight became explicit, the session was tightened to return
  a typed `BACKEND_CONSTRAINT` refusal rather than leak an execution exception.

## Scope boundary

This is private Xvfb/Tk/XTEST evidence and a runtime integration candidate. It is
not yet a claim of general Linux desktop support, WSLg acceptance, Wayland
support, Unicode/IME correctness, arbitrary application semantics, Windows or
macOS control. Release support remains the frozen Golden Desktop v3 WSLg path
until separately accepted on the intended supported host.

## Next promotion gate

Run the same candidate on the Ubuntu CI Xvfb fixture, then merge the additive
runtime backend if exact published bytes match the tested source. After merge,
actual WSLg application acceptance remains a separate release/support gate.
