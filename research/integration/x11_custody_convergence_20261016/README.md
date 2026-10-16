# X11 custody proposal: recover public evidence, retain rejection

2026-10-16. Main comparison: `1761692b3799fdad0abe52f3deb2e24a3f8a993a`.
This is saved-data convergence of [closed, unmerged PR #7148](https://github.com/Unjuno/agent-interface/pull/7148),
**not adoption of its backend patch or qualification of current native control**.
No historical actor, producer, auditor or formal allocation was replayed.

## Recovered material and decision

| Published material | Retained bytes | Interpretation |
|---|---|---|
| [V4 report](members/v4/REPORT.md), [original proposal](members/v4/PROPOSAL.json) | 320 complete public members; compressed and decoded JSON hashes match the five original comments | Historical 57-method construction pass, original baseline/wrong-index failures and reader/construction repairs remain. Six original Git inventories/indexes are explicitly omitted. |
| [Continuation 33](members/c33c34/continuation33/RESULT.md) | Part of 71 complete public members from two original comments | Stable-ID XI1 encoding observation leaves generation and competing-owner questions. It does not qualify a server or input device. |
| [Continuation 34](members/c33c34/continuation34/RESULT.md) | Same capsule; first failing actor and marker-only repair are separate | Conditional inert read-access suppression can produce a valid zero-state reply and false V4 release verification. Original expected failure and unrelated transport error remain. Sixteen reference/seal originals are omitted. |
| [Author suspension](context/5973813117.txt) | Exact public comment text | V4 adoption/application HOLD supersedes its earlier offer. The former reviewer-count procedure in archived records is historical, not a new repository requirement. |
| [N02 summary](context/5973902271.txt), [audit correction](context/5973922245.txt) | Exact public comment texts only | Native baseline missing-UP result is reported, but its complete original raw/source package is **not** recovered here. Seven original audit blind spots and later ten-control correction remain explicit. Do not certify this result from the summaries. |

The two transport objects in `capsules/` and all **391** expanded members in
`members/` match their published hashes. These are the publisher's projected
public bytes: workspace/interpreter/username substitutions were already applied
before publication. The capsules preserve distinct original/private hashes;
those hashes do not authenticate unavailable original files. All **22 omissions**
remain declared in [PROVENANCE.json](PROVENANCE.json), alongside seven source
comment URLs and their body hashes. No omitted file is fabricated from a hash.
These are selected recoverable publications, not all 51 PR comments or every
historical revision/intermediate proof.

## Current-source relationship

[The crosswalk](CURRENT_SOURCE_CROSSWALK.json) compares all 32 expanded V4
`candidate_final` source images with the pinned main: 23 byte matches, six
changed files and three missing historical test modules. Current files are read
from Git blobs; historical data are never installed over them. The archived
`sources/baseline` is V4's predecessor candidate, not today's main: its five
listed methods differ structurally from current main. Neither matching files nor
saved 57-method results establish a current-runtime pass.

Current source still needs a qualified solution for uncertain explicit UP,
wheel/side-button obligations, source/device association, read-access semantics,
generation and competing owners. The current backend's tracked-key/three-button
readback is not whole-server neutrality; [#7258](https://github.com/Unjuno/agent-interface/pull/7258)
already retained that scope boundary. Do not repeat that experiment as a new
discovery, or adopt V4's XI2 readback merely because its earlier suite was green.
The conditional false-clear and generation/routing residuals are design
constraints for [#17](https://github.com/Unjuno/agent-interface/issues/17),
with task effect/recovery and matched economics still tracked in
[#59](https://github.com/Unjuno/agent-interface/issues/59) and
[#57](https://github.com/Unjuno/agent-interface/issues/57).

## New saved-only checks

Run only these new entry points from the repository root:

```text
python -B research/integration/x11_custody_convergence_20261016/read_saved.py
python -B research/integration/x11_custody_convergence_20261016/test_saved_publication.py
python -B -O research/integration/x11_custody_convergence_20261016/test_saved_publication.py
```

The stdlib reader imports no recovered module and executes no actor. It checks
both historical compressed/JSON pins, member length/hash/byte identity and exact
expanded inventories. Four new methods pass normal/-O, including six copied
negative controls: changed/missing member, extra member/fabricated omission,
changed/truncated capsule. Original missing-fixture RED errors, corrected RED
failures and final streams are in `checks/`. Explicit exceptions keep these
checks active under `-O`. [CONDITIONS.json](CONDITIONS.json) records the initial
prose-matching parser rejection and repaired strict fence decoding. This is an
ordinary posthoc construction, not a newly preregistered scientific result.

`PUBLIC_BYTES_VERIFIED_ONLY` does not rerun historical semantic auditors,
restore omitted reference/dependency files, attest loaded memory, authenticate a
native server, measure release time or score task effect. The outer SHA256SUMS
covers this publication's added metadata and receipts as well as recovered
bytes. Runtime/workflow/default behavior is unchanged.
