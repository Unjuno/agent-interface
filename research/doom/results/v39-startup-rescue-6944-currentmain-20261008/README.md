# V39 startup-custody evidence rescue (#6944)

This current-main successor preserves the historical evidence from source PR
[#6944](https://github.com/Unjuno/agent-interface/pull/6944), head
`686bb56f8e9d16aaf37f1b1b65fd177d05ab11b8`, without adopting its controller or
active regression tests. Five source packages are copied byte-for-byte into
their original paths:

- `research/doom/v39_startup_composition_b04b_v2/`
- `research/doom/v39_startup_diagnostics_b04b_v3/`
- `research/doom/v39_startup_poll_custody_b04b_v6/`
- `research/doom/v39_startup_reader_repair_b04b_v4/`
- `research/doom/v39_startup_repair_59_20261003_01a0ff33/`

## H/T/D/C/U

- **H:** V39 startup failures can leave journals, readers, pipes, or cleanup
  callbacks with uncertain ownership; diagnostics and cleanup must not replace
  the original startup exception or falsely claim retirement.
- **T:** Preserve the original ordinary/fake-boundary results, first failures,
  raw records, source snapshots, receipts, negative controls, and custody
  projections. This rescue does not rerun the experiment or decode-and-execute
  any archived script.
- **D:** Archive only. No active controller, active test, workflow, or runtime
  behavior is promoted. The archived packages contain no active `.py` files;
  quoted scripts remain `.py.txt` data.
- **C:** The historical checks are scoped to their recorded fixtures, doubles,
  or owned-child cases. They do not establish a complete current-main startup
  lifecycle, a hard OS deadline, live game/model behavior, task effect, or
  physical input release.
- **U:** Current-main code composition and integration remain unqualified. The
  original source PR conflicts in the controller, test, and native integration
  catalogue paths; its own record requires fresh content review and application
  gates before any code promotion.

## Rescue integrity checks

The 321 files in the five packages were read back against the source branch's
Git blob IDs. Four package manifests were independently checked by bytes and
SHA-256: 49, 43, 43, and 178 entries. The poll-custody archive's two base64
payloads were checked against their recorded text hashes, decoded gzip sizes
and hashes, and member counts (35 and 46). No historical artifact was edited.

This is evidence preservation, not a new experiment. Obstac/container execution
was not attempted for this archival-only transfer, and no new PASS is claimed.
