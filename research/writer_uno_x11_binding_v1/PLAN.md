# Writer UNO/X11 document binding v1

H: positional pairing of independent UNO-component and X11-window enumerations can bind the wrong Writer document, while fresh UNO Frame activation followed by stable `_NET_ACTIVE_WINDOW == input focus` can bind document RuntimeUID/URL to the correct XID.

T: fixed launch order `a-target.odt,b-sidecar.odt`; separate fresh private Xvfb/Openbox/LibreOffice Writer sessions. Compare positional zip pairing against activated binding. Both type the same suffix over XTest at 12 ms/character. Independent post-input UNO readback scores A and B. Candidate binding activates A, B, A and requires stable A-XID identity and A/B distinct XIDs. Formal schedule after source freeze: 5 paired blocks = 10 sessions.

D: PASS if all 5 positional sessions reproduce wrong-target effect and all 5 activated sessions produce exact A=`bookkeeperoffice`, B=`sidecar`, with empty physical input. If positional ordering changes, retain outcome rather than tuning; candidate still requires 5/5 exact.

C: title corroboration and LibreOffice/Openbox behavior may be environment-specific. Activation itself is an application control side effect and is not a generic OS window-identity API.

U: private X11 only; no Wayland/Windows/macOS/IME/model/token claim. UNO research observation is not yet a product dependency decision.
