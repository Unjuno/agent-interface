# Separate Xvfb window-selector diagnostic

This is an environment probe only. It did not open the pilot workbook, edit cells, save a document, or consume another #34 experiment case.

Image: `issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393` (`linux/arm64`). A blank LibreOffice process was started under Xvfb `:98` with a fresh profile, `--network none`, read-only root, and writable `/tmp` tmpfs.

Observed:

- `xdotool search --onlyvisible --class soffice` returned no IDs.
- `xwininfo -root -tree` listed `0x20000b "VCL ImplGetDefaultWindow": ("libreoffice" "LibreOffice 7.4") 1280x800+0+0`.
- `wmctrl -l -p` returned `Cannot get client list properties. (_NET_CLIENT_LIST or _WIN_CLIENT_LIST)` because no window manager exported the EWMH list.

Interpretation: the pilot's `soffice` class selector is not a valid visibility observer for this image; an independent root-tree check can find the VCL window. This does not retroactively prove the original pilot's window visibility. The pilot's frozen audit STOP remains unchanged.
