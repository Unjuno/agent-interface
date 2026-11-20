# Mindustry v160.2 asset readiness — bounded preflight

At current main `cfb691b3b890d01c0b24fd1cd988609a62c4dd2a`, the official
GitHub v160.2 release metadata identifies `Mindustry.jar` as 87,022,576 bytes
with SHA-256 `7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539`.
The release asset was downloaded into the untracked local `outputs/` directory;
its observed size and SHA-256 exactly match the release metadata. The binary is
not committed to the repository. A read-only ZIP integrity pass verified all
5,386 entries and found no CRC failure; the manifest names
`mindustry.desktop.DesktopLauncher`. The game code was not executed.

Both canonical save files on current main resolve to Git blob
`7663b25633d853a257fbb407723fe85579120111`; the recorded expected size is
23,335 bytes and SHA-256 is
`8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed`.
A read-only host lookup also found two matching save copies in a retained
worktree; that worktree was not modified or taken over.

Ubuntu WSL has Python 3.12.3, `Xvfb`, and `xvfb-run`, but no Java runtime. No
Java runtime was installed or downloaded. Therefore the v160.2 game was not
launched; no GUI/input, model/provider call, Docker operation, or formal
allocation was used. This is an asset-readiness pass and a launch-prerequisite
HOLD, not a live Mindustry result.

The next required setup step is to make an approved Java runtime available in
the isolated WSL environment, then freeze and run the no-input setup smoke. Do
not infer task success or economics from this packet. Conditions, release
metadata, exact commands, WSL preflight output, and packet hashes are retained
here. The downloaded JAR remains in the ignored local output directory above.
