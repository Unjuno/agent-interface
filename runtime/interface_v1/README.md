# Runtime interface v1

One side-effect-free discovery/doctor facade for Linux, Windows and macOS.

`python -m runtime.interface_v1`

The probe may inspect native API availability, display/session metadata and
permission state. It never emits input or captures a screenshot and therefore
never turns native API presence into a support claim.

- Linux: detects X11/Wayland session candidates; the merged X11 adapter is still
  separately gated for supported-host use.
- Windows: inspects user32 API availability and desktop metrics only.
- macOS: inspects CoreGraphics/ApplicationServices availability and permission
  preflight state where the OS exposes it; it does not prompt for permission.

Native effect backends remain separate promotion gates under Issue #564.
