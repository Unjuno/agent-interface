# Recorded Win32 task effect R07

Status: `STOPPED_BEFORE_DISPATCH_VALIDATION_BUG`. R07 is a retained excluded
attempt, not a task-effect experiment. Its fresh fixture was visible and the
foreground PID/HWND/title matched, but the runner compared the raw source hash
with the PNG image-block hash instead of comparing the PNG with
`observation.artifact.sha256`. It stopped before dispatch; no input was sent.
The used run/call IDs are retired and must not be replayed.

The exact conditions, source, returned public observation and image, recorder
bytes, fixture metadata, foreground check, stop receipt, and excluded setup
attempts are retained here. The fixture was closed through CUA; its window
disappeared from the window inventory. R07 is superseded operationally by the
separately frozen R08 run, but its history is preserved unchanged.

R07 provides no action, task effect, release, horizon, efficiency, recovery,
MAP01, or Research Preview evidence. SHA-256 entries for the raw packet are in
`SHA256SUMS.txt`.
