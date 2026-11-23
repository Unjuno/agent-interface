# Win32 public runtime CLI Notepad task R03

**Disposition: one dispatch attempted; task failed before input.** The repaired
zipapp built at source revision `0831e690b14b78347c2eb39c8eb39a7aced26276`
is 790,952 bytes with SHA-256
`56ced08ca480dd2217d606328fefda5d30d0ff0d304b6db4c4bfa2431a4e596b`. Its 65
packaged source files match exact blobs from baseline main
`22aba58c276141401a7688be335be5191ec661b9`. Doctor selected `win32-v1` with
side-effect authority false. Public CLI pre-observation returned a fresh
capture and consistent target generation; the independent image shows the
empty Notepad document.

The single public CLI dispatch returned `execution_failed` with
`foreground focus verification failed (SetForegroundWindow=False,
observed_foreground_hwnd=25432038)`. `program_emissions=0` and
`backend_emissions=0`; there was no task effect. The retained terminal release
receipt is verified, with no keys/buttons down or unknown and no release
errors. The required read-only post-observation returned, and the independent
file oracle found exactly 0 bytes (SHA-256 of the empty file
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). The
exact target HWND/PID/process identity matched through the attempt and was
closed normally after evidence capture.

This result shows the packaging omission is repaired sufficiently for public
Win32 observation, but this host denied dispatch-time foreground admission.
R03 is not retried. No task-success or comparative-efficiency claim follows.
The next separate attempt must bring the experiment-owned window to the
foreground through ordinary Computer Control before dispatch and retain that
activation as a setup event.

See [CONDITIONS.md](CONDITIONS.md) and all raw requests, reports, images,
target receipts, and the empty task file under `run/` and `target/`.
