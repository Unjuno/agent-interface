# Dormant-branch recovery status — Procedural Operations Facility v0

Recovered additively from remote branch
`research/procedural-ops-facility-v0-20260928` at
`74778c43ca0b6a9ef6f2d5a4a3f8db440b48873d`. This record describes construction
and deterministic instrument checks only; it is not an Agent Interface
performance result.

## Local container verification (2026-10-02)

- `docker build --platform linux/amd64` succeeded after the whitespace-only
  EOF cleanup recorded in this PR. Final image ID:
  `sha256:fb792b14e8901ca7c53c8582c602eb856081626d9d1833ba45f98331508b6b87`.
- `docker run --rm --network none --entrypoint
  /facility/run_tests_container.sh procedural-ops-facility-v0-recovery:20261002`
  passed: C core tests 6/6; Python tests 9/9; Xvfb reference smoke
  `CONTAINER_GUI_PASS` with state hash `d45401b07d81e288`; fixed-seed mechanics
  and render benchmark; and the deadline-axis sweep.
- Final-tree rerun observed 250/250 reference episodes (2,558.523 episodes/s)
  and 250 rendered frames (686.941 frames/s). The 5-seed sweep observed 0/5 successes
  at 600 ticks and 5/5 at 10,800 ticks. These are instrument construction
  measurements under the private reference controller, not candidate efficacy.
- The container was linux/amd64 while OrbStack host was linux/aarch64; Docker
  warned that execution used a different host platform. Debian packages were
  installed by unpinned `apt-get` during build, so this is not a byte-reproducible
  dependency image. The repository's Ubuntu CI should independently run the
  committed workflow on its native runner.
- No model, GPU, external agent, hidden-seed formal evaluation, or production
  runtime was used.

## Sibling branch triage

The older, similarly named remote ref
`research/procedural-operations-facility-v0-20260928` at
`644fe8f2dd0ccfaeb02e677f1eb17a3cb6f76799` was not merged into this package.
Its committed tree contains 11 files but omits the `src/main.c`,
`src/facility.c`, and `src/facility.h` named by its Makefile. Its own Docker
build stopped at `make clean test` with `No rule to make target 'src/main.c'`;
zero tests ran. Its exact tip is now preserved by annotated tag
`archive/recovered/procedural-operations-facility-v0-incomplete-20260928`
(`644fe8f2dd0ccfaeb02e677f1eb17a3cb6f76799`), and only the remote source ref
was removed after confirming no associated Issue/open PR and verifying the
tag's peeled commit. The archived prototype must not be described as validated
or equivalent to this implementation.
