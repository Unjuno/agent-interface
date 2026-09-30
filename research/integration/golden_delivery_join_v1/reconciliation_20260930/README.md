# Golden delivery-join integration reconciliation

This is bounded engineering validation of the existing #5284 correction, not a
new experiment or a rerun of its consumed 800-row allocation. The original
44-file capsule, frozen sources, raw rows, AUDIT.json and publication helpers are
preserved byte-for-byte from PR head `b85d4c9565ebcb40e71965520ddcd63dfd41bba7`.
Both predecessor branches remain intact.

## H / T / D / C / U

- **H:** Historical source identity can remain strictly checked while current
  adapter semantics are tested against the evolved real runtime package
- **T:** Verify the original P2 audit's nine-file import/source closure at
  `8588ae768b9d83e77d5a797fd2c7cfb588747cde`; compare all four current frozen P2
  files to those originals; separately test the current adapter and re-audit
  already-retained delivery evidence. Do not run `run_matrix.py`
- **D:** Historical original audit PASS; current original #5284 correction passes
  22/22 unit methods and the unchanged five-case P2 semantic fixture; preserved
  capsule audit is byte-identical; six packaging methods and eleven identity-guard
  methods pass. New exact-ref hosted CI remains a separate integration gate
- **C:** The former CI audited the mutable working adapter against historical
  blob `b72fa220...`. Main already contained `bd6e1731...`, so the source-pin failure
  predates this candidate. Historical PASS does not qualify the current adapter
- **U:** Local checks use CPython 3.12.14 and a Git-blob-verified sparse source
  reconstruction. No full-suite, new Docker, GUI, model, live transport, task-success,
  performance or runtime promotion result is claimed by these local receipts

## Source and result separation

The candidate adapter remains original blob `4009bf4b3b79b34936fa5fff800875b1f19a8b75`.
The historical manifest, audit, test fixture and README are unchanged. A new
identity checker uses explicit exceptions rather than optimizable assertions and
pins the real historical API/selector dependencies as well as its adapter and
fixture. It rejects altered current frozen files instead of allowing a historical
checkout's success to conceal damage to current evidence.

The revised P2 workflow fetches current CLI/selector source subtrees plus the
runtime initializer if present, and a separate exact nine-file historical checkout.
The pinned checkout action uses blob-filtered sparse fetches. Both current test
modules and the five-case fixture have no skip-on-missing-source fallback.

The original audit runs unchanged against historical sources natively. The same
fixed Python container image verifies source identities and then runs historical
five-case and current five-plus-22-case checks separately. It uses read-only mounts,
no network, one CPU, 512 MiB and a 64-process limit. Git installation is unnecessary
inside that container because the identity checker performs Git-blob hashing;
this is equivalent decomposition of identity and semantic checks, not execution
of the original Git-dependent audit script inside the container. This one job has
a ten-minute cap. The original delivery-join workflow separately checks its capsule.

## Retained local evidence

The accompanying `local/` directory preserves argv, exit status, stdout, stderr and
resource-bound receipts for every construction check, including first failures:

- Main adapter: six of 22 delivery methods fail, exposing hidden nested evidence
- Original P2 audit on main: source-pin assertion fails before semantic checks
- Historical original audit: five cases/two manifest source blobs pass
- Original candidate on current dependencies: 22 methods plus five semantic cases pass
- Capsule: 44 files / 1,243,413 member bytes restored; original audit byte-identical
- Packaging: six methods pass; identity guard: eleven methods pass, including
  tamper, missing-source, symlink, unexpected-import, size and optimized-Python controls
- The new helper's initial RED check before implementation remains retained

Each local execution batch used one CPU, a 512-MiB address-space bound, 55 CPU
seconds and 60 wall seconds. The longest observed batch was approximately 1.22
seconds. Formal runner invocations were zero. An initial materialization request
was rejected before process creation for an oversized argument list; four-file
source-materialization batches recovered it without running any experiment.

The capsule SHA256 remains
`fc826618decbd7b5314a4a137474c32c2a89049cdf173b6d5c217fc8b63dba8e`;
AUDIT.json SHA256 remains
`b4ad197a9319b0baba395765da32a7d9ec53b5cf945cd300f590049fe216b69f`.
Current input snapshot was `fc048dc3a69bfb4521de9bfb80da18226b2f26fd`; relevant
source readback at `9fc98feb617c26fe1baa7ecc4decd43b69df8601` found all checked
runtime, test, workflow and frozen P2 file identities unchanged.

An independent static review found no blocking issue in this reconciliation's
source separation, current import closure, preservation guards or workflow.
Earlier #5284 hosted checks used merge ref `830b3c3f98ce3af0ac2a7600832656500237feeb`;
they do not qualify this new wiring. Keep the integration HOLD until the new
candidate's applicable exact-ref CI and review pass. No frozen manifest edit,
formal-result replacement, old-branch deletion or broader issue closure is implied.


## First hosted attempt and checkout-only correction

Initial integration head `2dafb3c7cb1a6f9f50eb10a8df5366625791bc90` passed the
new split P2 gate (including its pinned-container checks), PR-event Native MCP,
CLI/build platform jobs, X11, review and retained-evidence/replay checks. Its
nested-failure workflow also passed syntax and both tests, after approximately
eight minutes in the slim image's Git-less REST-archive checkout path. That is a
passing correctness check with an inefficient source-materialization step.

Golden-delivery run [36749414542](https://github.com/Unjuno/agent-interface/actions/runs/36749414542)
was cancelled at its five-minute limit during full checkout. All three substantive
steps (current regression, packaging controls and retained raw re-audit) were
skipped. This is the remaining execution gap; it is not a scientific/semantic
failure. Duplicate push Native MCP run
[36749297802](https://github.com/Unjuno/agent-interface/actions/runs/36749297802)
spent approximately 4m39s in checkout, passed relay-host tests, then was cancelled
about 19 seconds into shared integration checks without a retained result artifact.
That duplicate is not a pass; the PR-event Native MCP run passed. No manual retry
or formal-workflow dispatch was requested.

The follow-up changes only checkout setup in the two affected workflows and adds
this explanation. Golden retains its original three commands and five-minute cap.
Nested retains its exact pinned base image and both Python commands, adds an
explicit five-minute cap, and installs only Git from the image's official Debian
repositories after fail-closed TLS trust-store/CA-bundle checks. There is no package
upgrade command, extra privilege or insecure certificate option. Git becomes part
of the ordinary CI environment; this is not a formal-experiment identity claim.
Both workflows use complete relevant CLI/selector source subtrees and the complete
study/capsule directory. Missing required sources fail instead of skipping tests.

Preservation is precise: **20 of the original 21 #5284 paths remain byte-identical**;
its Golden-delivery workflow now has the reviewed checkout-only delta. The adapter,
twelve-test module, every scientific source/result/capsule byte and all capsule
helpers remain exact. Nested-failure's two-test fixture is unchanged. Neither live
workflow is bound by the frozen/packed source manifest or plan. An independent
review found no blocking issue in the exact two-workflow delta. The first CI
outcomes remain in their original runs; the corrected new head needs its own CI.
