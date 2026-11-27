# R32 — pre-input stop: WSLg read-only socket directory

**Disposition: STOP_PREINPUT, zero test input.** The public caller and XRes preflight did not start. R31 showed that `/tmp/.X11-unix` lacked the sticky bit; R32 preregistered a reversible correction, but WSLg exposes the directory as read-only and the `chmod 1777` attempt failed with `Read-only file system` before starting Xvfb.

Postflight confirmed the directory remained mode `0777`, the existing X0 inode was unchanged, and X88 was absent. No X session or input was altered. This is an environment boundary only; it is not a runtime or task-effect result. R32 is not retried. A pinned WSLc container remains the next viable route because its private `/tmp` can be writable without changing the WSLg host directory.
