# Preparation failures before measurement

All entries occurred before the frozen 20-case measured allocation. No measured case was run or replaced.

1. Offline python-xlib 0.33 installation initially omitted its `six` dependency. Repaired by installing retained `six-1.17.0` and python-xlib wheels with `--no-deps`.
2. Initial screenshot detector began workspace scanning at x=160, clipping the left A rectangle and producing a wrong click coordinate. Fixed detector workspace x-start to 40.
3. Pointer-click selection construction did not reliably select the Inkscape object. Replaced construction selection with standard Inkscape selector + Tab traversal. This changes only setup/mutation mechanism before freeze; the measured question is selection-context change, not pointer targeting.
4. Legacy dark-handle selection scoring did not match the current Inkscape theme. The current UI emits a blue selection marker at A's left boundary. Frozen revalidation therefore requires unchanged pure-red A/B centers plus >=100 blue marker pixels in the A-bound marker strip. Construction observed 276 marker pixels.
5. Final excluded construction: stable moved A by +10 SVG units and B by 0; switch moved A by 0 and B by +10; both had successful A revalidation and empty final keys/buttons.
