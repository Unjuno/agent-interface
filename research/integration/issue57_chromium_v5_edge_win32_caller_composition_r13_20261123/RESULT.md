# R13 result: Windows denied foreground acquisition

Date: 2026-11-23 (Asia/Tokyo)

## Outcome

**STOP before visual capture or task input in all four planned combinations.**
The unique Edge window and profile ownership check passed, but both
standard-Python and optimized runs failed at the existing Win32 backend's
`focus("edge")`: `SetForegroundWindow=False`; the observed foreground HWND
remained the original window (`25432038`). R13 did not retry, call an
alternate focus API, or send any task input.

All four raw records show zero screenshots, native operations, POSTs and
effects. Empty cleanup releases verified, the test profiles were removed, and
the original foreground window remained/restored. No model/provider calls
occurred. The Edge build was `157.0.4341.60`.

## Interpretation

The test harness cannot acquire the Windows foreground from this execution
context. This is an OS permission/focus boundary, not evidence about the
Win32 input path. The implementation did not bypass it. To proceed with a
desktop-pixel experiment, the target must be foregrounded through a legitimate
interactive activation path; otherwise the R13 records remain a valid stop.

## Frozen artifacts

- Protocol: [PROTOCOL.md](PROTOCOL.md)
- Harness and protocol freeze: commit `624b3041571ea61121bf47ed130726e6d17d7b60`
- Standard and optimized raw cases: [raw](raw)
- Raw SHA-256 manifest: [SHA256SUMS.json](SHA256SUMS.json)
