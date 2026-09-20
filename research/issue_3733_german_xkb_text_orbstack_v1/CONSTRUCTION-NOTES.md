# Construction notes — Issue #3733

These probes are not formal rows and are not evidence for or against the text-delivery hypothesis. They are recorded because the first setup attempt exceeded Issue #3733's construction-only boundary by applying layouts before the formal freeze. No Agent Interface candidate code or XTEST/text input ran in these probes.

1. Image `issue3257-xtest-candidate:20260920`, config ID `sha256:7ca3c5aa2531ebfd53736b3866a2c3ac9c71109aaad2eb29ab30ac3ac9a4b325`, Linux/arm64. Without explicitly enabling XKEYBOARD, Python-Xlib reported XKEYBOARD absent. `setxkbmap -layout de` returned 0 and printed a German rules resolution, while subsequent server query and core map remained US. This was an environment setup mismatch, not a candidate result.
2. A later construction probe enabled `+extension XKEYBOARD` and ran `setxkbmap`/`xkbcomp` before the freeze. It still observed the US server map. This command was exploratory only; its output was not retained as formal evidence and no candidate input was sent.
3. The frozen formal image below is a separate pre-existing OrbStack image with Xvfb, XKEYBOARD/XTEST, setxkbmap, xkbcomp, xev and Python-Xlib. On that image construction confirmed extension/tool availability and captured only the default baseline; no German layout was applied there before freeze.

The formal allocation has a fresh container and four fresh Xvfb server processes. Its outcome must stand alone. The preceding exploratory attempts are not pooled, counted as cases, or relabelled as formal results.
