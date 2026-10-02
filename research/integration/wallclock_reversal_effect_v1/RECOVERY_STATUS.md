# Current execution and publication status — Issue #4255

This record preserves the original frozen allocation and distinguishes its
preformal evidence from any formal result. It does not change #2442, #4387,
or the separate #4437 applicability study.

## Recovered source and local checks

The original branch contains the exact ten-file freeze/source/test package
for allocation `wallclock-reversal-effect-4255-20260923-01`. Its freeze says
formal invocations before execution were 0. The contract-only unittest suite
passed 4/4 in a local Python 3.13.5 ARM64 container. This checks only the
pure decision/admission contract; it is not an X11 effect test or formal row.

## Formal execution boundary

The frozen environment is Linux x86_64 with CPython 3.13.5 and Xvfb/XTEST.
The available Docker host is ARM64. Its Python 3.13.5 image lacks Xvfb and
Python-Xlib; the available Xvfb image has Python 3.12.3. No matching
x86_64/Xvfb environment was available in this recovery. The formal two-batch
allocation was **not started**; no formal results or scientific disposition
are claimed. Do not substitute an emulated or different-version run into the
frozen allocation without a separately documented environment decision.

No formal evidence is missing from an alleged completed run: formal execution
remains unperformed. Issue #4255 stays open, with the exact freeze and source
available on main for a worker to continue when the declared environment is
available. The issue's scope remains a synthetic X11 key-effect boundary,
not task success, physical HID telemetry, or production safety.
