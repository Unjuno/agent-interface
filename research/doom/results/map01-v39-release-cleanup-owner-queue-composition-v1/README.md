# PR #7385 cleanup overlap through the v10 owner loop

## H / T / D / C / U

- **H:** PR #7385's timestamped cleanup-overlap check should catch a cancellation or expiry release performed by the real v10 owner thread before a later queued explicit `up`; the exact #7378 parent should incorrectly verify that later call as ordinary.
- **T:** Run one cancellation race and one lease-expiry race through the exact v10 owner loop with Xlib calls replaced by an in-memory fake display. Force the owner thread to record cleanup before the adapter queues explicit `up`. Compare the pinned #7378 parent and #7385 candidate. Add a no-cleanup positive control.
- **D:** Candidate must observe verified cleanup timestamps inside the explicit-up brackets and set both `ordinary_release_candidate` and `owner_transition_verified` false; parent must produce the false-positive verification for each race; candidate must still verify a no-cleanup release.
- **C:** The owner scheduling, queue, cancellation/expiry checks, wrapper call, adapter code, and receipt adjudication are executed. Xlib is mocked, so this does not test a real display or native key state. A scheduled race only covers these two forced interleavings.
- **U:** No physical input, X server, game, model/provider, container, GPU, formal allocation, or external side effect. This is a deterministic constructor, not MAP01/live-control evidence.

## Result

The five-case composition suite passed. For cancellation and expiry, each parent case contains a verified `owner_release` before the queued explicit `up`, with exactly one mocked KeyPress and one cleanup KeyRelease; the parent nonetheless leaves its explicit-up receipt ordinary and owner-transition-verified. The #7385 candidate sees each cleanup timestamp inside the matching caller bracket and fails closed. Its no-cleanup control remains an ordinary verified release.

The result extends separate adapter-level and owner-loop tests by composing their exact boundaries. It does not demonstrate that a physical release reached an operating-system device, and it does not establish usefulness of task feedback or bounded recovery.

## Source provenance

- #7385 candidate backend: commit `23c228146a34ccaa71dafce153532703f04e4d23`, Git blob `98e69b734f85f13b956fbeb6922812f2959ee63d`.
- Exact #7378 parent backend: commit `fbed929f629dabaa9ae752019d0ee7151d4d2298`, Git blob `1515341081f3bbee2ca9587d1c937d398719f05b`.
- #7378 base wrapper: commit `fbed929f629dabaa9ae752019d0ee7151d4d2298`, Git blob `0ea631abcf6272f0538a9ef9198ad8069b47b464`.
- v10 owner: main commit `13bab54ea6d91978247ecc1b70e5060db752367a`, Git blob `341b3c01649943ddaad5f28431a792c4889cc36e`.

Upstream Git blob IDs identify source bytes. `SOURCE_MANIFEST.json` also records local byte counts and SHA-256 values; all four copied source files are checked for exact Git blob equality.

## Reproduction

Run `python -B capture_run.py`, then `python -B audit.py`. The suite uses only Python standard-library modules and installs a fake `Xlib` module in-process. It does not contact GitHub or invoke Docker, WSLc, X11, a GUI, or a model.

The test file is named `composition_test.py` and is under a result package, so it is not an automatically discovered runtime or broad repository test. It is explicitly run by `capture_run.py`.
