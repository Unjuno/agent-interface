# R12 result: PrintWindow returned a flat black frame

Date: 2026-11-23 (Asia/Tokyo)

## Outcome

**STOP before handle mint or task input in all four planned combinations.**
Both Python modes found and profiled the visible Edge window; Win32 capture
returned 756×488 pixels matching its client geometry. Visual inspection of
the retained PNG shows a fully black frame. The existing point mint correctly
refused the first target region as `FlatTargetRefused: visually flat target
region refused`; therefore no handle, admission, native input, POST or task
effect was produced.

All four raw run records contain zero native operations and zero POSTs. Empty
backend release receipts verify, the unique Edge profiles were removed, and
the prior foreground window was restored. The pre-input button state remains
unknown because no target action was run. Edge was `157.0.4341.60`; no
model/provider calls occurred.

## Interpretation

R12 proves dimensions alone do not establish valid capture pixels. The
`Win32Backend` `PrintWindow` path yielded black content for this Edge window,
and V5 refused it as designed. R13 will focus the isolated Edge HWND, then
capture the exact HWND client rectangle from the physical desktop with Win32
`BitBlt`; the crop will share the same origin and dimensions as
`window_client` input coordinates. The OCR target-presence admission guard
remains mandatory.

## Frozen artifacts

- Protocol: [PROTOCOL.md](PROTOCOL.md)
- Harness and protocol freeze: commit `62858d9855f68d39e7cdc7c205ce6b54dbea54ea`
- Standard and optimized raw cases: [raw](raw)
- Raw SHA-256 manifest: [SHA256SUMS.json](SHA256SUMS.json)
