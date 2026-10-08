# Audit-only preregistration — Issue #3595

## H/T/D/C/U

- **H:** An independently implemented raw-only auditor can reconstruct all
  three immutable Issue #3587 allocations despite the frozen v1 auditor's two
  faulty assertions (stale expected source revision and the Tk save callback's
  consumed KeyPress log event).
- **T:** Freeze `audit_v2.py` and its SHA before one execution in a separate
  network-disabled, read-only-root Linux/arm64 container. Mount the exact
  #3587 raw bundles and pinned archive/source manifest read-only; mount only a
  new audit-output subdirectory writable. Do not launch the public runtime,
  MCP server, GUI fixture, Xvfb, or send input. Reconstruct all original
  requests, reports, MCP image blocks, PNGs, independent effects, fixture
  events, source and archive identities, release, process/socket cleanup, and
  observation identity. Challenge at least seven distinct corruptions in
  memory; never modify raw inputs. Preserve original v1 `HOLD_OR_FAIL` bytes.
- **D:** `PASS_RAW_RECONSTRUCTION_ONLY` requires exact reconstruction of 3/3
  allocations against the pinned #3587 archive/source/image, all request/report
  and PNG/artifact hashes linked, saved marker and event evidence consistent,
  distinct initial/post observations, completed single dispatch with verified
  empty release, complete child/socket cleanup records, and at least 7/7
  corruption challenges rejected. Any mismatch is HOLD/FAIL. This cannot
  change #3587's official frozen-gate result.
- **C:** Exact same #3587 raw bytes, archive, manifest and container image. Only
  the new audit implementation and its output directory differ.
- **U:** No experiment rerun, model, live host, presentation acknowledgement,
  task-semantic model use, performance, token/cost, human-tempo, or broad
  reliability claim. Issue #3370 remains open.

## Frozen inputs

- Parent experiment source: `02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2`.
- Parent image: `sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`
  (`linux/arm64`).
- Parent archive and complete byte manifest: `prior_issue_3587/freeze/`.
- Original v1 audit output SHA-256:
  `f2efd3961994ea6fa889986c5065fb2ef7dc39051115a2fbaf3f4f50c61918af`.
- Parent raw allocation records and original v1 HOLD remain unchanged.

## Auditor construction test

Before formal audit, v2 was tested only on the excluded #3587 construction
allocation. It reconstructed the allocation with no per-allocation failures
and rejected all 10/10 in-memory corruptions. Aggregate status was HOLD solely
because that test corpus intentionally contains one construction row rather
than the three formal rows. The first construction test version exposed an
incorrect comparison between MCP-output PNG filenames and the runtime's
separately generated internal capture filenames; the corrected final v2 auditor
validates both by their bound bytes/hash. No formal raw bundle was read during
these construction tests.

