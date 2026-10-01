# Issue #3618 — public MCP explicit post-action observation

## H/T/D/C/U

**H.** On the pinned public portable stdio MCP path, one persistent connection
can perform `observe -> exactly one dispatch -> explicit read-only observe`,
save a unique marker, and return a new image reflecting the saved fixture.

**T.** Three fresh Linux/arm64 OrbStack allocations ran exactly once each using
the frozen archive, original fixture revision, and 100-ms action wait. Each
used `--network none`, a read-only root/source/archive/runner, private Xvfb,
one Tk fixture, and one persistent stdio MCP connection. One frozen independent
audit invocation stopped before reading evidence because its output directory
was bind-mounted at `/out`, so `/out.mkdir(exist_ok=False)` found it already
present. A separate audit-only successor (#3620) then ran the exact frozen
auditor once with a fresh child output path; it returned `HOLD_OR_FAIL`.

**D.** All 3/3 allocations returned exactly three calls in
`observe, dispatch, observe` order, discovered exactly
`interface_dispatch`, `interface_observe`, `interface_results`, saved the
exact independent marker, returned different initial/final observation IDs,
and had distinct initial vs final PNG hashes. In every allocation, the
dispatch-time PNG hash equaled the explicit post-observation PNG hash, and
human inspection of all three original-size final PNGs confirmed the visible
`saved:<marker>` text. Dispatch completed and release was verified empty; all
three Xvfb processes exited 0, fixture children were reaped, and X11 sockets
were removed. The raw-only auditor ran 122 checks and failed exactly three:
`formal-01:fixture-received-save-chord`,
`formal-02:fixture-received-save-chord`, and
`formal-03:fixture-received-save-chord`. Each event log contains `Control_L`
but no `s` keysym; saved effect and visible image do not override this frozen
input-event gate. Final disposition: **HOLD_OR_FAIL — not PASS**.

**C.** All three allocations used archive SHA-256
`e2f50196e7ac67372fd0c480dbee473d26cc84d33e09806900f1efe7c8e7e624`, source
revision `02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2`, OrbStack image ID
`sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`
(`linux/arm64`), frozen runner SHA-256
`c4ba017b3685d6d4ba78cea2b8ccbecdae6d769e41712da4c1c87e1b88135f75`, and
corrected auditor SHA-256
`aabf29ee6e8d5f74af2f5a0bf3b31df0f840462fe0f97a09db7a4f4b24f5e997`.
The archive and runner are unchanged from #3587. The excluded predecessor
construction row remains excluded.

**U.** This establishes scoped public-MCP operation and post-action image
delivery to the caller within these three container fixture runs, but the
frozen input-event gate did not pass. It says nothing about registered-host
presentation acknowledgement, model visibility/interpretation, latency,
tokens/cost, human-tempo benefit, broad GUI reliability, or completion of
#3370. Preserve #3587 as open.

Separately, the repository native integration-check runner
(`runtime/integration_checks/native.py`, used by
`.github/workflows/native-mcp-v1.yml`) passed 65/65 tests in a second pinned,
network-disabled OrbStack image with required dependencies. An earlier attempt
in the smaller portable-MCP image ran 65 tests but had 28 dependency-import
errors because NumPy was absent; the same unmodified suite then passed in the
native-MCP image. This supplemental check does not override the formal
raw-allocation audit.

## Preserved failures and reproduction

- `evidence/formal-audit-invocation-stop.json` records the first frozen audit
  process stopping before raw evidence because `/out` existed.
- `evidence/audit-successor-3620/` contains the one corrected-mount raw-only
  audit output. Its three event-gate failures are retained without relaxing
  the criterion or changing predecessor evidence.
- The exact runner, audit, archive, preregistration and source digests are in
  `freeze/`. All raw allocation files are covered by `evidence/manifest.json`.
- Reproduce each allocation using the recorded argv in
  `evidence/container-commands.json`; do not rerun these formal allocations.
