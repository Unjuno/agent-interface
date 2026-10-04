# SIGINT finalization checkpoint construction

Socrates review at fa7faafb2 resolved prior unstarted-reader and source-byte
identity findings, but found one new Important: unguarded poll/is_alive/time/
write boundaries could lose first STOP. Successor cd519586f defers SIGINT only
across child/thread cleanup and row plus STOP checkpoint writes, restoring the
old signal mask afterward. Final science PASS is written only after all four
cells; interrupted partial/finalization states retain a STOP checkpoint.

New subprocess control triggers real SIGINT immediately after actual row file
write returns, at the following checkpoint boundary. Masked SIGINT remains
pending; row and SUMMARY checkpoint finish, then pending SIGINT terminates
process nonzero. Earlier SIGINT after observed child still passes. This does not
prove SIGKILL, repeated signals during uninterruptible I/O, power loss, storage
failure or interruption during the post-audit final summary itself.

Host full suite18 PASS1.795s. Owned Docker f03-sigint-checkpoint-v1 full suite
18 PASS1.691s; 2026-10-03T23:59:08.968432706Z–23:59:11.059636860Z,
ExitCode0/OOMKilledfalse. Image560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Host/guest/container Git archive SHA matched
e3077fae232ce81a9a4df32eb635c819755dcd68be8518e022b3a194030061ed.
Networknone, readonly input/root, tmpfs, UID501. Resource settings CPU1/
memory1GiB/swap0/pids128 were configured, not read empirically during this run.
Raw v1 test log in methods/.

PASS_CONSTRUCTION_ONLY. Formal producer0, official auditor0, model0. New code
still needs independent review. Earlier reviewer and all first outcomes remain
immutable. No consumed allocation replay, production integration, or full
lifecycle claim.
