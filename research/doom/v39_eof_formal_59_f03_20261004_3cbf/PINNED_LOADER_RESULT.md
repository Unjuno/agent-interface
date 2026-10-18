# Source-hash to executed factory binding construction

Previous independent Important: hashing files followed by regular imports did
not bind the executed object. The loader now reads dependency bytes once,
checks each expected SHA256, compiles those same byte strings directly in
private module namespaces, and binds F02's exact `probe` import to the helper
module built from the pinned F01 bytes. It does not consult `sys.modules['probe']`
or pyc for either pinned source. Standard-library imports remain ordinary,
within the pinned image/runtime envelope.

Negative control installs poisoned `sys.modules['probe']`, invokes the actual
loader, and checks the returned F02 factory is from the compiled frozen source;
two one-byte mutations fail their respective pins. Fresh-process missing files
still create source-preflight STOP before importing dependencies. This does not
test every malicious Python loader hook or compromise of the image/interpreter.

Owned Docker f03-pinned-loader-v1 ran 17 package methods using -B -O -W error:
PASS0.834s; 2026-10-03T23:52:49.396171021Z–23:52:50.604813788Z,
ExitCode0/OOMKilledfalse. Host/guest/container archiveSHA256 matched
7dc5faf95dabdd6abd9bd77a4877f1addba3d51449edcacacfa3a2f6158afd5a.
Image560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Networknone, readonly root/input, tmpfs, UID501; CPU/memory/swap/pids set by
Docker but not re-read empirically in this run. Raw tool output in methods/.

PASS_CONSTRUCTION_ONLY, formal producer0, official auditor0, model0.
Earlier reviews remain immutable; all fixes need successor independent review.
The four-cell live result, actual-reader-active interrupt, final frozen delivery
custody and official saved-output audit remain outstanding.
