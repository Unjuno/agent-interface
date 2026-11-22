# Win32 R12 setup probe — Computer Use receipt arrived after timeout

**Disposition: `HOLD_COMPUTER_USE_ACTIVATION_TIMEOUT`; no native state read and
no input dispatched.** The probe started one disposable fixture on frozen main
`1b1ce38c943a5f93d94e6a9f028f5a50ceed618b` and waited at most 60 seconds for a
Computer Use activation receipt. It timed out, closed the fixture with exit
code 0, and restored the pre-launch foreground value.

Computer Use later selected the exact visible fixture window and returned a
screenshot after requesting activation. However, the probe result file was
written at 10:55:57 UTC and the separate activation receipt at 10:55:59 UTC.
The activation therefore arrived too late to be paired with a live native
foreground or key-state readback. Do not infer that the foreground transition
or SHIFT neutral state was verified. The late receipt is retained separately
as `computer-use-activation-post-stop.json`.

The pretrial manifest has four entries and no mismatches. The raw manifest has
seven entries and no mismatches. This is an excluded setup attempt, not an
expiry/recovery result. The next run needs a longer activation window and must
record native foreground and witnessed SHIFT state before cleanup.
