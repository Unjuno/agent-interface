# XRes resource-base reuse diagnostic r03

**Result: `PASS_DIAGNOSTIC_RESOURCE_BASE_REUSE_IDENTIFIED`.** This is a
two-display construction diagnostic on ordinary Ubuntu WSL. An isolated user
and mount namespace provided a private tmpfs `/tmp` with a mode-1777 X11
socket directory; shared `/tmp` remained unchanged. Both scenarios used
private Xvfb servers with TCP disabled. The probe sent no input events and
used empty key/button obligations. It is not release, task-effect, timing,
reliability, WSLc, or MAP01 evidence.

The first Xvfb attempt had no bystander after owner PID 418 exited. The
prestarted helper PID 417 then opened its X connection at the retired owner's
resource base 6291456. XRes returned PID 417 at that base, and
`x11_cancel_worker` returned `stale_owner_identity` with nested
`owner_client_disconnect.reason=resource_base_reused` and `UNKNOWN`.

In the second display, replacement client PID 426 acquired the retired owner's
base 6291456 before helper PID 421 connected. The helper used base 8388608;
XRes still returned PID 426 for target base 6291456, and the worker again
returned `stale_owner_identity` with nested
`owner_client_disconnect.reason=resource_base_reused` and `UNKNOWN`.

This identifies both branches of the earlier PID 439 observation: an
observer can itself reuse the just-freed base, or a separate client can reuse
it first. XRes reports the current PID at a resource base, not the identity
generation of the client that formerly owned it. The current code's rejection
is conservative and prevents release from being inferred from a PID mismatch.
The experiment does **not** show whether a different protocol can confirm
owner disconnection or whether release should be authorized after that proof.

For both cases the receipt kept `release_confirmed=false`, `task_success=null`,
and `replay_allowed=false`; no key/button release was attempted because the
obligation sets were empty. Each scenario is a single synthetic trial. The
complete JSON, raw logs, conditions, source hashes, and exact local runtime
patch readback are retained beside this file.

## Reproduction and source

Run `run-isolated.sh` with the repository and packet paths in Ubuntu WSL. It
uses an unprivileged user/mount namespace and a private tmpfs, then runs two
Xvfb instances and `probe.py`. The current branch and runtime files were
modified locally during the run; see `host-source-readback.txt` and
`runtime.patch.host.txt`. WSL Git could not resolve this Windows worktree's
absolute `.git` pointer, so the runner's in-WSL `git diff` snapshot is empty.
The exact Git stderr is retained in `workspace-git.stderr.log`; the host-side
diff and per-file SHA-256 values provide the source identity.

The next code change is still subject to review of the written design spec.
After review, add a Fake X/public-caller case for observer-owned base reuse and
decide explicitly whether this identity evidence can establish owner-client
disconnection. Keep release confirmation, replay authority, and independent
task success as separate claims.
