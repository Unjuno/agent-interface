# Setup attempts (no candidate input was sent in any attempt)

- **a01:** private namespace and overlay mounts succeeded, but the command referenced `/usr/bin/Xvfb` rather than the privately extracted binary. Output: `bash: line 7: /usr/bin/Xvfb: No such file or directory`.
- **a02:** corrected the binary path; Xvfb stopped before creating a server because private extracted `libXfont2.so.2` was missing.
- **a03:** added the pinned `libXfont2`/fontenc archives; Xvfb and `xkbcomp` startup stopped because private `libxkbfile.so.1` was missing.
- **a04:** added the pinned `libxkbfile1`; Xvfb started and `XOpenDisplay` succeeded. The setup script wrote its PASS receipt but its wrapper then encountered a trailing carriage-return shell error. No input was sent.
- **a05:** normalized the shell script to LF and repeated only the no-input startup check. Exit 0; `XOpenDisplay True`; private socket directory mode 1777; shared directory mode 777 and its external socket was not exposed to the namespace; zero candidate runs, zero input events, and no package installation.

All setup attempts used separate retained logs. The formal candidate has not yet run at the time this note was written.
