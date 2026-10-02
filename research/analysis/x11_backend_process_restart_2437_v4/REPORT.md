# Issue #2437 — Allocation 04 preparation record

## H / T / D / C / U

- **H:** The frozen Allocation 04 hypothesis is that after one backend process
  dies while F8 and Button1 remain logically held on the same live Xvfb, a new
  backend session may admit the still-valid stale request while lacking
  ownership of the orphaned button. This is a preregistered question, not an
  observed result.
- **T:** The source freeze specifies one private-Xvfb candidate invocation and
  one raw-only audit, with independent key/button observations, process/session
  identities, an unchanged server PID, and explicit independent cleanup.
- **D:** **NOT RUN / NOT EVALUATED.** The frozen record says the formal candidate
  was not invoked. This package contains no formal raw output or audit receipt;
  neither PASS nor FAIL is supported. Allocation 04 must not be pooled with
  Allocations 01–03 or 05.
- **C:** Local archive validation only: all four original source files match
  the source-branch Git blobs exactly; the synthetic `AuditorConstructionTests`
  passed 11/11. No candidate, raw-only audit, X11 preflight, Xvfb, GUI, input,
  Docker, or Obstac execution occurred in this validation.
- **U:** No conclusion about stale-request admission, held-control recovery,
  native desktop/compositor behavior, physical input, production safety, task
  quality, or latency. The frozen setup's stated WSL2/Xvfb limits describe a
  proposed experiment only, not an executed environment.

Source tip: `ea192babc76257a03899ac346e5602bfe2b14d35` on
`research/2437-backend-restart-multicontrol-v4-20261001`.
