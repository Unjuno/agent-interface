# Primary-assistant use of the native result boundary

2026-09-19. The primary assistant viewed `attempt-08/before.png`, chose
window-client point `[130,55]` and text `native991078`, then viewed
`attempt-08/after.png`. The public `dispatch_golden_v3` path executed native X11
input. The existing independent Tk fixture saved the exact text. No helper model
was used; main-conversation model usage is unavailable, not zero.

The result adapter returned program completion with unknown task success. The
separate effect-file scorer confirmed task success. A deliberately stale source
was refused first with `STALE_OBSERVATION` and zero backend emissions. Accepted
input ended with empty key/button release. Both owned processes were reaped.

| Local measurement, attempt 08 | Milliseconds |
|---|---:|
| Public dispatch call | 110.568412 |
| From call return to independent evidence read, including result persistence | 5.778866 |
| Call start to independent scored effect | 116.347278 |
| Whole harness lifetime through scoring/capture, including assistant wait | 25092.541249 |

These are one-run wall-clock measurements. They exclude subsequent assistant
inspection of the final image. The whole time excludes dependency preparation
and prior failed attempts. They are not a matched latency comparison, first
useful-feedback measurement, token saving or human-tempo result.

## Failures retained

1. Default Xvfb display allocation could not create the filesystem listener and
   repeatedly logged failure. The owned Xvfb was terminated; cleanup is recorded.
   The harness now bounds display readiness and uses a private abstract socket.
2. Tkinter was missing; no input program ran.
3. Local Tk extraction lacked libtk; no input program ran.
4. A shell extraction command expanded its filename incorrectly; libtk remained
   absent. No input program ran.
5. The extracted Tk libraries still required libXss; no input program ran.
6. Abstract display 0 shadowed an existing filesystem socket. Tk and Python-Xlib
   connected differently; capture failed with BadDrawable before dispatch. The
   harness now chooses a high private display and rejects a filesystem shadow.
7. Input completed and release was verified, but immediate scoring found no
   effect file and the final capture was unchanged. Application logs retained
   click/text events. This is a failed task result, not a successful save. It
   motivated waiting for independent evidence before tearing down the fixture.
8. A new session, explicitly re-grounded from its own image, completed with the
   bounded evidence read. The first accepted attempt was not replayed or resumed.

Attempt 08 polls only the effect file for at most two seconds. It sends no input
retry. Its success is consistent with application-event processing delay in 07,
but these two sequential attempts do not establish a controlled causal result.
All original files, including the large initial Xvfb error log, are retained.
`SHA256.json` covers 60 evidence/source files; this README is not in that manifest.
`final-source` is the final harness and relevant source snapshot, not an assertion
that every development attempt ran that same version.

## Reproduction and limits

On Linux/X11 with Xvfb, Pillow, python-xlib and tkinter available:

```sh
XAUTHORITY= python3 -m runtime.native_result_self_use --out NEW_DIRECTORY
```

View `before.png`, then write exactly one `request.json` with `point` (two integer
window-client pixels) and `text`. The harness waits up to 240 seconds. Its output
directory must not already exist. Use a different `--display-number` if needed.
Do not feed coordinates from an unviewed or different session.

This host lacked Tk packages. Ubuntu packages listed and hashed in
`dependency-packages.json` were downloaded and extracted with `dpkg-deb -x` under
`results-local/tk-local`, without a system install. The launch supplied:

```sh
PYTHONPATH=results-local/tk-local/usr/lib/python3.12:results-local/tk-local/usr/lib/python3.12/lib-dynload
LD_LIBRARY_PATH=results-local/tk-local/usr/lib:results-local/tk-local/usr/lib/x86_64-linux-gnu
TCL_LIBRARY=results-local/tk-local/usr/share/tcltk/tcl8.6
TK_LIBRARY=results-local/tk-local/usr/share/tcltk/tk8.6
```

The source sequence and revision are fixture-owned constants. There is no visual
target revalidation, guarded method reuse, interruption recovery, or cross-domain
comparison here. Native capture returns image metadata/hash; the harness uses a
separate capture to supply the assistant-visible PNG. That observation gap and
the visual-target admission bridge remain open. This does not satisfy Issue
#2337's complete live integration gate.
