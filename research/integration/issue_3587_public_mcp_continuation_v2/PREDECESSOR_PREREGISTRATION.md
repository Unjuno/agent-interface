# Preregistration — Issue #3587

## Frozen question

For a disposable Tk/X11 application, does the public portable stdio MCP route
support a caller-selected read-only continuation after an action, without
replaying input, and return a fresh PNG consistent with the independently
saved fixture state?

## H/T/D/C/U

- **H:** One persistent stdio MCP client can make `observe → dispatch → observe`
  using one MCP server process. The fixture independently saves one unique
  marker; the post-action observation is a new read-only observation with a
  distinct observation ID and PNG identity from the initial state. The
  dispatch-time in-program observation may be stale or current; it is reported
  as observed and not assumed.
- **T:** Exactly three fresh Linux/arm64 OrbStack containers. In each: launch
  private Xvfb and the committed Tk fixture, start one portable zipapp MCP
  server/client connection, discover tools, observe the 400×180 window, dispatch
  once (focus, click Entry at 70×55, type the unique marker, Ctrl+S, fixed
  100-ms wait, in-program 400×180 observation, final `release_all`), and after
  the action response issue one explicit 400×180 read-only observation. Retain
  all MCP text/image blocks, exact on-disk requests/reports, fixture effect and
  event log, process outcomes and PNGs. An independent auditor checks the
  frozen raw bundle after all allocations. No rerun or replacement.
- **D:** Scoped PASS only if there are exactly three formal allocations; each
  uses the pinned source/archive/image, discovers exactly
  `interface_dispatch`, `interface_observe`, `interface_results`, retains
  exactly 3 requests/reports in `observe, dispatch, observe` order, returns one
  image block for each call, independently saves the exact marker, completes
  dispatch with verified empty release, and produces a post-observation ID and
  PNG hash distinct from the initial observation. The dispatch-time and
  post-action PNG hashes must agree in this fixture allocation. All request,
  report, PNG, effect, source, archive, child-reap and X11-socket checks must
  pass the independent raw-only audit. In addition, inspect each original-size
  post-action PNG and confirm that the displayed saved marker exactly matches
  the independently recorded marker. This visual inspection is a human-audited
  check, separate from image hashes. Any mismatch is preserved as
  STOP/HOLD/FAIL, without repair or rerun.
- **C:** Same committed source, portable archive, image, fixture geometry,
  program shape, operation order and wait across all allocations. Only unique
  marker, XID, random call/observation IDs, timestamps and generated paths vary.
  This is not a transport comparison.
- **U:** Container-only integration/correctness evidence. It does not establish
  registered-host availability, host presentation acknowledgement,
  model-visible receipt/interpretation, semantic use by a model, broad GUI
  reliability, useful-feedback latency, model tokens/cost, human-tempo benefit
  or efficiency. It cannot pass or close #3370. Source/binding/lease values
  remain caller supplied.

## Frozen inputs

- Main source revision: `02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2`.
- Portable build is generated deterministically from that committed revision;
  `freeze/manifest.json` binds every included source file.
- Portable artifact SHA-256: `e2f50196e7ac67372fd0c480dbee473d26cc84d33e09806900f1efe7c8e7e624`
  (157,384 bytes).
- OrbStack image: `issue-3573-portable-mcp-orbstack:20260920`, image ID
  `sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`,
  `linux/arm64`.
- Runner SHA-256: `c4ba017b3685d6d4ba78cea2b8ccbecdae6d769e41712da4c1c87e1b88135f75`;
  auditor SHA-256: `5aaa31729068403e3bf52579ca6b16252395a3aaa7c3b54f992c3fa46b6b54d5`.
  All three digests are listed in `freeze/SHA256SUMS`.
- Formal run command uses `--network none --read-only`, a read-only source
  mount and archive mount, one fresh writable evidence mount, and read-only
  runner mount. `OBSTAC_IMAGE_ID` and `OBSTAC_PLATFORM` are fixed environment
  fields recorded by the runner.

## Excluded construction

One pre-formal disposable construction allocation established harness
feasibility. It is not a formal row and cannot be pooled with the formal
allocations. It is retained separately in `evidence/construction-excluded/`.
