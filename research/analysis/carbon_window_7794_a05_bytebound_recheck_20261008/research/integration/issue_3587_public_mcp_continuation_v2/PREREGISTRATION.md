# Successor preregistration — Issue #3618

## Hypothesis and test

This repeats the exact #3587 narrow integration question after correcting its
independent auditor's source-revision expectation. For three fresh disposable
Tk/X11 allocations, one persistent public stdio MCP connection will support
`observe -> one bounded dispatch -> explicit read-only observe`; the fixture
will independently save each unique marker, and the final observation will
have a fresh identity and image distinct from the initial state. No input is
replayed by the final observation.

## H/T/D/C/U

- **H:** The pinned portable stdio MCP path correctly retains and serves an
  explicit read-only post-action observation after exactly one dispatch.
- **T:** Exactly three sequential Linux/arm64 OrbStack containers, each with
  network disabled, read-only root/source/archive/runner, private writable
  `/tmp`, and a fresh per-allocation evidence mount. Each launches private
  Xvfb and one Tk fixture; one persistent MCP client discovers tools, observes
  once, dispatches exactly once (focus, click, unique text, Ctrl+S, fixed
  100-ms wait, in-program observation and `release_all`), then explicitly
  observes once more after the dispatch response. After all three, run the
  frozen independent raw-only auditor once in a separate no-network,
  read-only-root container. No retries, replacements, or tuning.
- **D:** Scoped PASS only if all three complete with exactly the documented
  tools and 3 calls in observe/dispatch/observe order; exact independently
  saved marker and received input events; one image block per operation;
  distinct initial/final observation IDs and image hashes; dispatch image
  matching final image; completed dispatch with independently verified empty
  release; complete request/report/image/effect/source/archive/process records;
  and all auditor checks passing. Original-size final PNGs are also inspected
  manually for the exact visible saved marker. Any failure is retained and
  reported as HOLD/FAIL/STOP; never rerun a formal allocation.
- **C:** Exact archive, runner, fixture source revision, container image,
  geometry, operation order, program and wait. Only per-run marker, XID, random
  identifiers, timestamps and generated evidence paths vary.
- **U:** Container-only correctness/integration evidence. No registered-host
  acknowledgement, model visibility or interpretation, latency/cost,
  human-tempo benefit, broad reliability claim, or closure of #3370.

## Frozen identity

- Current-main base at freeze: `48b7e660c40cef5bef17beeb2777b2b29705d69b`.
- Runtime source embedded in the unchanged portable archive:
  `02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2`.
- Archive: 157,384 bytes, SHA-256
  `e2f50196e7ac67372fd0c480dbee473d26cc84d33e09806900f1efe7c8e7e624`.
- Runner: SHA-256
  `c4ba017b3685d6d4ba78cea2b8ccbecdae6d769e41712da4c1c87e1b88135f75`.
- Auditor: source expectation corrected to the archive's embedded revision;
  hash recorded in `FREEZE.json` after finalization.
- OrbStack image ID
  `sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`,
  `linux/arm64`. Container Python is `/usr/bin/python3` (MCP, Tkinter and
  Pillow imports verified); network is `none`, root is read-only.
- Fixture source is a clean worktree at the embedded archive revision. The
  fixture module SHA-256 is recorded in `FREEZE.json`.

Formal evidence uses `evidence/formal-01`, `formal-02`, and `formal-03`, each
mounted alone at `/evidence`. The frozen runner writes one allocation to the
mount root. The auditor reads all three directories from `/evidence` and writes
once to the fresh `/out` mount. The prior #3587 construction allocation and
frozen auditor mismatch are excluded and preserved unchanged.
