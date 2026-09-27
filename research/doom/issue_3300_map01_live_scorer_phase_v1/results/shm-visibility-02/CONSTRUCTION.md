# SHM visibility 02 — read-only shared snapshot is not a live clock

Disposition: `PASS_CONSTRUCTION_ONLY_SHM_SNAPSHOT_STALE`.
This result falsifies the narrow proposal that a separate read-only POSIX
shared-memory reader exposes a live tic in the current passive condition. It
does not satisfy the live scorer phase witness required by #3453.

## H / T / D / C / U

- **H:** a second process can read `GAME_TIC` or `MAP_TIC` directly from the
  ViZDoom shared-memory segment and obtain a live clock that is independent of
  the stale Python API getter.
- **T:** OrbStack Linux/arm64; ViZDoom 1.3.0 image ID
  `sha256:4320dd483b24ea91c1481f12fd5799c903d9daa99a517b994f607037098ea41d`;
  official Freedoom 0.13.0 WAD SHA-256
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
  One fresh hidden MAP01 `ASYNC_SPECTATOR` session, 35 Hz, no buttons,
  explicit `new_episode()`, `+viz_debug 2`, no DISPLAY, network disabled,
  read-only root and 128 MiB noexec/nosuid tmpfs. The observer opened the
  advertised POSIX SHM segment using `shm_open(O_RDONLY)`, mapped it with
  `mmap.ACCESS_READ`, and sampled both tic fields plus the Python API getter
  for 1.5 s. No action, controller tic/update message, keyboard or mouse input
  was sent by the probe.
- **D:** retain every monotonic read bracket, both SHM counters, Python API
  tic, SHM identity/size/open status, exact ViZDoom 1.3.0 struct offsets,
  hashes, image/WAD identities, independent audit and test output.
- **C:** `shm_open` succeeded read-only; segment size was 2,634,640 bytes.
  Across 481 reads spanning 1,499,109,015 ns, shared `GAME_TIC` remained 4,
  shared `MAP_TIC` remained 1, and API episode tic remained 1. The independent
  audit returned `PASS_CONSTRUCTION_ONLY_SHM_SNAPSHOT_STALE`, zero errors;
  both focused audit tests passed in the isolated arm64 container.
- **U:** `GAME_TIC=4` is a retained shared-state snapshot, not the live internal
  engine gametic. This observer therefore does not establish internal clock
  phase, scorer overlap, an uninstrumented 35 Hz distribution, or permission
  to start the one-shot 120-row formal allocation. The API and SHM may share
  the same message-driven refresh boundary.

## Source basis and offsets

The pinned upstream ViZDoom 1.3.0 `VIZGameState` declaration is
`src/vizdoom/src/viz_game.h` (git blob
`b86015faf2f7a764e795214f9ce0323eabebda88`); it declares `GAME_TIC`, then
the seven-region count from `viz_shared_memory.h` (blob
`2f51ff3741dc942d616aa984b4d8cc52cc7664f8`), and later `MAP_TIC`. Under the
container's LP64 ABI the derived offsets are 152 and 216 bytes respectively.
In `viz_main.cpp` (blob `07885474717bae7b4c40f2c06619ebf0f2e3832b`),
`VIZ_Tic()` advances internal `vizTime`; `VIZ_GameStateTic()` is conditional
on `vizNextTic`. In `viz_game.cpp`, that function copies engine `gametic` and
`level.maptime` into the shared structure. Thus the shared counters are
refresh-on-message state, not guaranteed per-tic live counters.

`shm-visibility-01/` preserves the earlier exploratory capture. It predates
the structured raw output and did not freeze the executed probe hash. Run 02
is the reproducible, hash-bound capture used for the audit and conclusion.
Neither run is formal allocation data.
