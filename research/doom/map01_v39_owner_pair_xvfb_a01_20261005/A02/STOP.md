# A02 STOP

- Outer runner invocation returned exit 20.
- Xvfb was started as `:98`; the runner readiness loop incorrectly polled
  `/tmp/.X11-unix/X99`, so it never invoked `candidate.py`.
- `candidate.py` invocation count: 0. Auditor invocation count: 0.
- The runner terminated its Xvfb process and retained `xvfb.log` and
  `xvfb.exit` under `results/A02/`.
- Xvfb log contains only nonfatal xkbcomp unknown-keysym warnings. The
  decisive defect is the frozen runner's mismatched display number.
- A02 is not retried. A03 is separately frozen with the runner display/socket
  corrected and a fresh output path.
