# Allocation 03 construction-01 report

**Disposition:** `PASS_PRIVATE_XVFB_RESET_TERMINATION_CONSTRUCTION_ONLY` (strictly scoped; no formal input).

The frozen one-shot probe completed without timeout. A distinct child mount namespace (host inode `4026532221`, child inode `4026532241`) mounted tmpfs exactly at `/tmp/.X11-unix`, source token `none`, directory mode `01777`. Xlib connected to private display `:98` and read `640x480`; the X98 socket existed while connected. After the sole client's normal close, Xvfb exited naturally with code 0 within the frozen three-second bound. No signal fallback was used. The persisted WSLg socket metadata was identical before/after: mode `0777`, inode `2`, device `38`; a post-run check found no `Xvfb` process and no host `X98` socket.

The independent auditor emitted `PASS_PRIVATE_XVFB_RESET_TERMINATION_CONSTRUCTION_ONLY`, 12 checks, and rejected all six declared corruption mutations. Its stderr was empty. The `audit.exitcode` capture file is empty because the shell wrapper failed to preserve the child status; therefore the auditor's explicit JSON result is retained as the decision evidence, while the missing status capture is a provenance limitation. An earlier auditor launch attempt had an incorrect relative path; its empty stdout, error stderr, and exit code are preserved as `audit-launch.*`. It did not modify or rerun the experiment. The corrected auditor invocation read the frozen source and raw result once; no probe retry or post-probe source edit occurred.

The Xvfb startup log includes non-fatal `xkbcomp` warnings about symbol conflicts and unavailable keysyms and explicitly says these errors are not fatal to the X server. This construction does not test XKB behavior or any key input.

## Scope

One Arch WSL2 host, private Xvfb, one Xlib query/close, and local WSLg socket-directory metadata only. This does not validate XKB remapping, fixture effects, WSLg/Windows GUI input, concurrent use, the separately frozen #5236 formal rows, or product/general X11 reliability. Allocation 02 remains unchanged.

## Frozen source

- Base main: `c45e1947e498dce08abfb27e459e610054a0602e`
- Source commit: `bfe8f8d07693b595e38f49cdba1aa38fc14575a1`
- Branch: `research/issue5243-terminate-reset-20260930`
- Source files and blob IDs are recorded in the prelaunch freeze comment on Issue #5243.
- Preflight: 5/5 standard-library tests passed in Arch WSL and in Docker `python:3.13-slim-bookworm`.

## Raw evidence SHA-256

| File | SHA-256 |
|---|---|
| `result.json` | `E4EAD363D0F8B7BE5B082E5E3BBFEE11894EB5F6EE646E8E07663EBB0D0CAA14` |
| `child-record.json` | `561CD414E53F414F1B608925C5B7067DC11E0CE02665B4B05CE7805AFECCF60D` |
| `xvfb.log` | `12DCABF0449B9FF85D589B86D110C814777977DACA56E7BA8EC300C5334FE397` |
| `audit.stdout` | `4FD135BD050F4179767E252E2AC1979CE371F97730672516392120E658DFC202` |
| `audit.stderr` (empty) | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `audit.exitcode` (empty; capture limitation) | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `audit-launch.stderr` | `B6CE5F28C55A902CA96AFD36F670757ED7C1FC7E0A36265A1D4A3EE0EB9B1A9F` |

The first failed-launch stdout was empty (`E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`); its captured exit code file SHA-256 is `01BA4719C80B6FE911B091A7C05124B64EEECE964E09C058EF8F9805DACA546B`.
