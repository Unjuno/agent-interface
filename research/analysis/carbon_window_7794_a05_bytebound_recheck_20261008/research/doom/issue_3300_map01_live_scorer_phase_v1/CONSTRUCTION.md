# Excluded OrbStack construction records

Formal allocation status: **not started**. These runs are setup and measurement
instrumentation checks only. They are not included in the 120 scheduled rows,
and none is a scoped PASS for live-coherence reliability.

## Construction-05: current construction candidate

- OrbStack, Linux arm64 image `sha256:3ae8a1ecab2ade30da6f1efcbdb4310931f59f0d01568b5d0bff7f360e8cd5e3`.
- Python 3.11 slim Bookworm base pinned by Dockerfile digest;
  ViZDoom 1.2.3; official Freedoom 2 v0.13.0 MAP01 WAD SHA-256
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- `--network none --read-only`, `/tmp` tmpfs, WAD mounted read-only.
- Three separate `ASYNC_SPECTATOR` sessions (idle, frozen CPU load, delayed
  read), with no game buttons. Empty `advance_action(1)` calls drive only the
  engine clock; a second thread records tic edges. The unchanged scorer was
  called once in each construction row.
- All 3 rows initialized and cleaned up; all observed positive clock progress;
  independent raw-trace reconstruction identified the scorer-attempt phase in
  all 3 rows. Measured construction clock estimates were 36.51, 35.87, and
  33.34 Hz, respectively. These small-sample values are diagnostics, not
  acceptance thresholds or natural phase estimates.
- Raw: `results/construction-05/raw.jsonl`; container stdout/stderr:
  `results/construction-05/container.log`; raw SHA-256
  `bd5d6b698f42fd988803f0ec4cb9f8a522c7a5d88476ed932bbb23452d81e220`.

## Construction-06: committed-source image reproduction

After committing and rebasing the exact source, rebuilt the image and repeated
the excluded construction check so image provenance matches committed code.

- OrbStack Linux arm64 image
  `sha256:c9f5fdd7c63bff4d3e4cd4d4953f99bcd8d5ae83dc2ea94972e475453d9e7a43`;
  same pinned base, ViZDoom and read-only WAD described above.
- All three sessions advanced and cleaned up. Independent reconstruction
  identified the phase for all 3/3 scorer attempts. Clock estimates: idle
  36.58 Hz, CPU load 33.96 Hz, delayed read 33.32 Hz (construction only).
- Raw: `results/construction-06/raw.jsonl`; container output:
  `results/construction-06/container.log`; raw SHA-256
  `2d90899bc705a45823806ad1f0e1ec6fb95050e61bd6f1a1dc4faffd42e63c1c`.

## Earlier construction and retained setup stop

- `construction-04` used image
  `sha256:2e37c21c7be8b68c0877c9b2594ef6cea49f5efe5d3e7e0c0bf4d943b4a5ddd6`.
  Its 3 rows advanced and cleaned up; the first audit implementation rejected
  phase bounds because it underestimated adjacent-edge timing uncertainty.
  The raw trace is immutable (`bae08036f2f19f6cc9a844d9a1bd9d1328f9a528ec70eddb9e91d6bfbfdac494`).
  Corrected interval arithmetic now reconstructs 3/3 phases from that same raw
  trace; construction-05 independently exercised the corrected build.
- `construction-02` preserves a genuine read-only-root setup stop: ViZDoom
  attempted to create `./_vizdoom/_vizdoom.ini`. Its image/log/raw are retained;
  the corrected invocation uses a writable tmpfs working directory.
- `construction-01` and `construction-03` predate final scorer call/phase
  instrumentation. Keep their original bytes and do not pool or cite them as
  current-candidate measurements.
- The benign PulseAudio “Failed to create secure directory” messages appear in
  container logs; they did not prevent game initialization, clock progression,
  scorer calls, or cleanup.

## Immutable stop from the parallel #3456 probe

The merged #3456 construction artifact remains unchanged. Its separate async
clock reconciliation found all 36 rows and 108 scorer calls at static tic 14,
so that artifact supports only scorer-call-path and same-tic audit mechanics;
it does not demonstrate an advancing clock. See main's
`research/doom/issue_3300-obstac-async-phase-probe-v1/CLOCK_RECONCILIATION.md`.
Construction-05 is a new, separate clock-driver setup and is not pooled with
those rows.

## Excluded autonomous-clock diagnostics

Additional OrbStack runs used the same pinned Freedoom MAP01 WAD and ViZDoom
1.2.3, with no button/action calls during each observation window:

- Hidden window + `ASYNC_SPECTATOR`: 21 reads across 1.14 s all remained at
  tic 1.
- The persisted repeat is `results/autonomous-clock-01/container.log`
  (image `sha256:9480a5cce161df033e22c1e306a3319e819e76e981b52c88fdcd2fbedebdda43`,
  raw-output SHA-256
  `73472cc7e62a0b9c9c04cfdcc62d5fc1a88bb96015a572c942d62c73be3bb763`).
- Visible window on a manually started Xvfb server + `ASYNC_SPECTATOR`: 21
  reads across 1.15 s all remained at tic 1. Virtual display alone did not
  start autonomous episode progress.
- Hidden window + `ASYNC_PLAYER`: 21 reads across 1.12 s all remained at tic
  1. This is a diagnostic only and not a replacement for the required
  `ASYNC_SPECTATOR` condition.
- One startup `advance_action(1, True)` changed tic 1 to tic 3 in 31.6 ms;
  the following 21 reads across 1.14 s all remained at tic 3. A one-time kick
  is insufficient.
- Persisted at `results/autonomous-clock-02/container.log` (same image; raw
  output SHA-256
  `e24543a18b18514c55e4205a91ddf61f752be00700da29aa5fa4040a8a6de7a6`).
- `SDL_VIDEODRIVER=dummy` with a visible window crashed ViZDoom (signal 11,
  address `0x8`) before producing rows. This is an infrastructure stop, not a
  game/scorer result. An initial `xvfb-run` wrapper also remained waiting;
  direct Xvfb startup subsequently worked but did not advance the clock.

These checks show that this exact headless fixture does not progress on its
own, even with an X server. The construction runner's separate
`advance_action(1)` thread is therefore required to produce advancing tics in
this container. It sends an empty action (the button list is empty), but it is
still an explicit clock-driving intervention. Formal results must be
interpreted within that setup and must not be generalized to autonomous
async-mode progression. The raw construction-05/06 rows retain the driver's
step timings and separate probe timings so API contention remains auditable.

## Scorer invocation correction

The initial draft made three external calls to a scorer which already performs
three internal attempts. That would measure a different, up-to-nine-attempt
procedure and did not match #3453. Before formal collection, the frozen
schedule and auditor were corrected to invoke the unchanged scorer exactly
once per episode and classify a row failure only when its three internal
attempts are all incoherent. Construction rows remain one invocation each and
their original raw data are unchanged.

The final candidate records mode/ticrate/button readbacks, each scorer start's
lateness relative to the requested phase target (subtracting the declared
delayed-read control), and an independent interval phase estimate. The probe
and empty-action driver both call the same ViZDoom instance concurrently; raw
API timing and driver-step timing are retained, and this remains a scoped
clock-driving fixture rather than a passive autonomous-clock claim.

## Construction-07: corrected one-invocation candidate

After aligning the schedule to one invocation of the original three-internal-
attempt predicate, this excluded run used image
`sha256:84766e2edb264a8c4b3b6e96ab3b9b7b95a6dd580eec96e5e28e5c0b88f56536`
(arm64). All three sessions reported mode readback `ASYNC_SPECTATOR`, ticrate
35, and an empty button list; each made exactly one scorer invocation, returned
on its first coherent internal attempt, reconstructed that attempt's phase,
and completed cleanup. Measured rates were 36.24, 35.54, and 37.39 Hz; scorer
call spans were 587,173 ns, 136,491 ns, and 699,789 ns. Requested-target
execution lateness was 948,075 ns, 3,333,772 ns, and 3,749,440 ns. These three
values validate instrumentation only and do not establish the formal
distribution or boundary resolution.

- Raw: `results/construction-07/raw.jsonl`, SHA-256
  `b0e1c62b16fc13a072f6d441b295d07ee4a691f5556fc633d7fbe646c3157e92`.
- Container stdout/stderr: `results/construction-07/container.log`, SHA-256
  `53a12617676dfb543bc9419c607adb92d474103b8eef9f7d371c178e3efb8ba5`.
- The committed raw was independently audited inside OrbStack image
  `sha256:8a0cfcf80951991e54072fc60a6b7c954ac31f1e5b9c344a194a4f893c8a732d`
  using `audit.py --mode construction`. Result:
  `PASS_CONSTRUCTION_ONLY`, 3/3 rows and phases reconstructed, zero errors,
  zero warnings; the audit's `formal_allocation` is false. Retained at
  `results/construction-07/audit-run-01/audit.json` and
  `container.log`; both have SHA-256
  `48cdb06d7b588a036cfb4879440fe9211ddf0abb46a4fb0e3334e3d2fe70d28e`.

Construction-06 was also passed through the new construction-scoped auditor.
It reconstructed all 3 rows and all 3 phases with zero warnings, but returned
`HOLD_CONSTRUCTION_AUDIT` because that older raw schema predates the explicit
`phase_target_execution_lateness_ns` field. Its audit and container output are
retained at `results/construction-06/audit-run-01/`; audit JSON SHA-256
`e0cb0a209fee75d01795ed1ea16c9e7a1b29ff176317a9a02c9bb9ed47aec2a9`. This is
an expected schema hold, not a rewritten construction-06 result.

## Gate before formal freeze

The initial 1.2.3 candidate used a continuously calling action driver and was
not frozen. Follow-up 1.3.0 passive-clock and scorer-snapshot checks found a
stale Python-visible tic through 2 s waits, followed by a 71–72 tic catch-up
after one action refresh; the exact scorer returned first-attempt coherent in
3/3 passive intervals. See `CLOCK_WITNESS_RECONCILIATION.md`. These are
construction findings only and still do not identify the live tic phase at a
scorer getter. Formal rows, a formal one-shot guard, and a policy conclusion do
not exist.

The follow-up also checked the separate ViZDoom `get_server_state()` API in
three new 2 s passive sessions (155/157/155 samples). Its `ServerState.tic`
remained equal to `get_episode_time()` and `get_state().tic` (all fixed at 3),
so it is not an independent live-clock witness in this fixture. The prior
read-only-cwd startup failure and an initial wrong-binding-name diagnostic are
retained as separate numbered runs. See the same reconciliation report for
raw/log hashes and the container audit. A separate three-session boundary
characterization found that all API views remained at tic 3 across the passive
wait, then advanced together to 77/75/75 after one endpoint action. ViZDoom
1.3.0 source confirms that `get_state()` / `get_server_state()` are wrapper
snapshots refreshed by the explicit action boundary; it does not resolve why
the `MAP_TIC` read stayed fixed during the wait. Formal remains 0/120.

## Construction-clock-22–27: passive-clock alternatives and repaired driver check

These remain excluded from the formal allocation and are kept as separate
numbered experiments.

- Run 22 repeated a 2 s no-action window in three headless ViZDoom 1.3.0
  `ASYNC_SPECTATOR` sessions. All three tic APIs stayed at 1 in 150/154/160
  samples. The unchanged scorer returned first-attempt coherent at tic 1 in
  3/3. This did not establish whether the engine itself was paused.
- Run 23 compared implicit post-init state with an explicit `new_episode()`
  call in three matched pairs. All six sessions stayed at tic 1 through 2 s;
  explicit calls took 81.5–83.4 ms and `is_new_episode()` remained true. The
  explicit start call alone did not unlock passive progress.
- Run 24 is a retained pre-session infrastructure stop: the old local image
  tag lacked a file that the runner hashes (`/opt/phase-probe/Dockerfile`). No
  game session or scientific row was produced.
- Run 25 produced three raw rows but is retained as
  `FAIL_CONSTRUCTION_INTEGRITY`: it used the package-bundled WAD instead of
  official Freedoom 0.13.0 and omitted the image ID. Do not interpret or pool
  it.
- Run 26 rebuilt a corrected linux/arm64 image, mounted the official
  Freedoom 0.13.0 WAD read-only, and supplied the exact image ID. The existing
  empty-button `advance_action(1)` driver produced positive clock rates
  (33.25/34.54/36.92 Hz) and the independent auditor reconstructed the exact
  scorer phase in 3/3 strata, `PASS_CONSTRUCTION_ONLY`, zero errors/warnings.
  This validates the intervention-driven instrumentation, but does not satisfy
  the later explicit no-advancement-API requirement and cannot authorize
  formal collection.
- Run 27 tested a single empty `set_action([0]*9)` assignment after explicit
  episode start against three matched sessions with no assignment. In all six
  headless ViZDoom 1.3.0 sessions, tic views remained `(1,1,1)` through at least
  2 s; the exact scorer returned at tic 1 and cleanup was complete. No
  `advance_action` or `make_action` was called. The one-time empty action
  assignment did not unlock passive tic progression.
- Run 28 paired `available_buttons=[]` against nine registered-but-unused
  buttons (3 sessions per arm). All six sessions stayed at tic tuple `(1,1,1)`
  for 2 s, exact scorer succeeded 6/6, cleanup 6/6, and no set/advance/make
  action API was called. Audit disposition is
  `HOLD_BUTTON_INVENTORY_DID_NOT_UNLOCK_PASSIVE_TIC`, zero errors.
- Run 29 paired hidden MAP01 `ASYNC_SPECTATOR` vs `ASYNC_PLAYER` sessions
  (three per arm), each explicitly started and observed for 2 s without
  set/advance/make calls. Both modes remained fixed at their per-session
  starting tics (first pair tic 2; next pairs tic 1); all three APIs agreed,
  exact scorer returned and cleanup succeeded 6/6. Audit:
  `HOLD_BOTH_ASYNC_MODES_PASSIVE_TICS_STATIC`, zero errors. This does not
  authorize changing the formal issue's declared mode.

Exact commands, raw results, audits, container logs, and per-run digests are in
the corresponding `results/construction-clock-{22..27}/` directories.
