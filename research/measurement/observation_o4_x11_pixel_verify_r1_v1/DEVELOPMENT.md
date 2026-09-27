# #1847 construction / development provenance

This file records preformal harness work and is not formal scientific evidence.

## Retained construction stop

The first manual private-X11 probe stopped before any scientific row. `Xvfb` was running, but `python-xlib` attempted to open the nonexistent default `/opt/xvfb/.Xauthority` and raised `XauthError`. Formal consumption remained zero.

The harness-only repair was to use a private `Xvfb` with `-ac -nolisten tcp` and set `XAUTHORITY` to a fresh empty file for every session. No category, verifier predicate, gate, seed, threshold, ROI, or formal schedule changed.

## Pixel-signature preflight

Three fresh private Xvfb sessions reproduced byte-identical independent Xlib ROI signatures:

- GREEN: `6c7367a67820f53d7ee4f49ff6a6814cdaafafce1a2b748b068efc6880aeb355`
- RED: `63fd8c2d48370b1ef4e0489848856d6c3acaa77eab16c94bab2d19ee32e1cfb3`
- GRAY: `7e4463276f3f4a8c2c9951998d3f7c0d13413bf0543b324bb263e4ef302e245b`

Each read was 24x24 ZPixmap / 2304 raw bytes through a separate Xlib connection.

## Excluded construction

Seven fresh sessions, one per formal category, passed the independent construction audit. Construction timing is descriptive only and excluded from formal efficacy claims.
