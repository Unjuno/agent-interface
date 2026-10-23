# Native Win32 HWND reuse discriminator R01

This frozen, one-shot probe creates two hidden Win32 `STATIC` windows
sequentially on the same Python thread. It reads each HWND's real owner PID,
GUI-thread ID and process creation time through the production backend, reads
the production `target_generation()`, destroys the first window before making
the second, and destroys the second at the end. It never activates either
window, captures the desktop, or sends input.

The conditions and outcome discriminator were written before the native run.
`probe.py` refuses to run if `raw.json` already exists. A non-reused numeric
HWND is inconclusive for reuse and will not be retried.

Outcome categories are defined in `conditions.json`: same HWND + same owner
identity + equal generation demonstrates the known alias; same HWND with a
different generation is a scoped successful discriminator; different HWNDs
mean reuse was not observed in this single trial. All categories remain
limited to this Windows host, class, process, and schedule.

## R01 outcome

The first hidden HWND was `50923368`; after its destruction, the second was
`50988904`. Both had the same process and GUI-thread identity, and both were
destroyed with `IsWindow` false afterward. Their generation digests differed
because the numeric HWNDs differed. The frozen outcome is
`NO_REUSE_OBSERVED_IN_THIS_SINGLE_TRIAL`; the 7-check structural audit passes.
This does not challenge or validate the known same-numeric-HWND reuse alias,
and no retry was made. Exact inputs and outputs are in `conditions.json`,
`raw.json`, and `audit.json`.
