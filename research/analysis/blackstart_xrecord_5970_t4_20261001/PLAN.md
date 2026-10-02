# Issue #5970 T4 — X RECORD delivery-boundary diagnostic

## H / T / D / C / U

- **H:** X RECORD's server-side `FromServer` KeyPress/KeyRelease capture can determine whether XTest transitions were delivered by the X server even when the exact-source-derived window observer records none.
- **T:** Reuse only the exact hash-frozen #4135-derived app and observer from merged T3. In a fresh private Xvfb, establish an X RECORD context filtered to delivered KeyPress/KeyRelease events, confirm recording is active, dispatch one Shift press/release pair, unconditionally attempt cleanup release, and verify terminal Shift-neutral keymap. Retain raw RECORD response category and bytes. Independently parse those bytes and reconstruct the source archive.
- **D:** `PASS_RECORD_DISAMBIGUATES_OBSERVER_GAP` only if X RECORD contains one press and release with the tested keycode/time while the selected observer stream has zero events, app stream has the same pair, cleanup release was attempted, and terminal keymap is neutral. If RECORD also sees zero, classify `HOLD_NO_SERVER_DELIVERY_EVIDENCE`; if observers agree or streams are malformed, retain the corresponding distinct outcome. No timestamp order creates causal edges.
- **C:** One cooperative Tk window, one synthetic Shift pair, one Xvfb server, one X RECORD context. RECORD evidence is scoped to server-delivered core events; it does not prove physical HID history, semantic truth, authorization, production behavior, or task benefit. Docker Desktop container is preferred if its engine becomes usable; otherwise disclose WSL2/Xvfb fallback.
- **U:** Whether the T3 gap is window selection/propagation, event subscription, observer scheduling, RECORD overhead/perturbation, or an XTest-specific difference; whether RECORD is practical in production; concurrent input behavior; recovery benefit.

## Safety and one-shot policy

T0-T3 and #4135 formal artifacts remain immutable. Candidate/auditor each run once with unique output. RECORD is active only inside a fresh Xvfb; release is sent in unconditional cleanup before querying neutral state. Missing RECORD payload is a HOLD, not silently inferred from the app event or timestamps.
