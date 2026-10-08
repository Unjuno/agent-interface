# V4 pre-container STOP: preservation review, 2026-09-30

## Disposition

**RETAIN_PRECONTAINER_STOP_ONLY.** Preserve all 23 original [PR #4918](https://github.com/Unjuno/agent-interface/pull/4918) files byte-for-byte. The retained outcome remains `STOP_DOCKER_CLI_USAGE_ERROR`, with `PASS_STOP_EVIDENCE_AUDIT` limited to the original STOP auditor's checks. This is not a precision result, a new allocation, or permission to retry the consumed v4 attempt.

This restoration closes a provenance gap: on intake main `6af2b750e37979de585d5a2e3c3d8e0c26926359`, the already-present [v5 result](../typed_readout_precision_boundary_1014_v5/evidence/construction_02/RESULT.md) points to its preserved sibling v4 STOP, while the v4 directory is still absent. The v5 result remains a distinct allocation and is not pooled with or substituted for v4.

## Independently verified static closure

- Pinned PR head: `49189c84238a81ba87b3592a86670c7de654a38a`
- Original frozen main: `f3dc0f18b0aaef241a6cd34124b68439c3434b05`
- Allocation: `typed-readout-precision-boundary-1014-v4-20260928-01`
- Method: read-only GitHub retrieval, exact byte hashing, and static JSON/text inspection. No repository program, model, GPU, container, GUI, workflow, probe, or auditor was executed for this review

All 23 original files recreate their advertised Git blob IDs exactly. Every declared byte count and SHA-256 matches: 8/8 entries in `SOURCE_MANIFEST.json`, 9/9 source entries in `FREEZE.json`, and 12/12 entries in `evidence/construction_01/EVIDENCE_MANIFEST.json`. These manifest groups overlap; their counts are not additional experiment samples. Original CRLF/LF distinctions were preserved, not normalized.

The exact 270,292-byte corpus has 64 JSONL records and SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`. Source, corpus, freeze and STOP evidence are all present in the PR. The separately listed model assets and container image are external prerequisites identified by metadata; they are not bundled or newly downloaded/verified by this preservation review.

The retained construction stdout is empty. Stderr is 109 bytes, SHA-256 `12bdcf916ade656d8940d40bc2efc62f8ed0a543cc19916b2585f81ba6176dda`, and contains Docker's `unknown flag: --rm` error. The invocation receipt records exit 125. The retained `STOP_AUDIT.json` and parsed `stop-audit.stdout.log` agree exactly, including an empty error list, zero recorded formal rows/forwards, and the declared no-retry outcome. Audit stderr is empty and its receipt records exit 0. These are readbacks of retained observations and receipts, not newly observed process outcomes.

## Limits of the historical execution evidence

The intended command in `FREEZE.json` includes `docker run`. The recorded attempted host command in `execution_context.json` omits `run` and is abbreviated with `...`; the exact complete attempted argument vector and host-wrapper program are not included. The retained CLI error is consistent with that reported invocation defect. Do not represent the intended frozen command as having successfully started a container.

The original STOP auditor reads an externally supplied raw directory and checks that it is empty. Git does not retain that historical empty directory; creating a new empty directory now would not independently establish its historical emptiness. Preserve the original zero-file statement as a retained observation, without claiming a repository-only historical filesystem reconstruction.

The auditor also trusts execution-context fields, checks for a candidate-name substring in a Docker snapshot, and searches a post-attempt GPU text snapshot for `0 %, 0 MiB`. These checks support only their recorded snapshot and declaration boundaries. The candidate command has no retained explicit matching container name, and a post-attempt idle sample is not a continuous no-execution trace. The GPU file also retains a literal backtick-n header separator; it has not been silently repaired or treated as a newly validated structured telemetry stream.

The Issue/PR's earlier 3/3 unit-test and 10/10 model-asset preflight statements do not have separate raw test/preflight process receipts in this 23-file delta. The model manifest, tests and frozen source are retained, but those historical execution statements were not independently repeated here. None of these limits turns a setup STOP into a scientific FAIL or PASS.

## H / T / D / C / U

- **H:** The missing v4 predecessor record can be preserved with complete declared source/STOP-file byte identity, without changing its first outcome
- **T:** Recompute Git blob identities and all three manifest groups; inspect the retained CLI error, invocation/audit receipts, and linkage from already-main v5 without executing either allocation
- **D:** RETAIN_PRECONTAINER_STOP_ONLY. All declared source and STOP evidence files are reachable and byte-consistent. The numerical precision hypothesis remains untested by v4
- **C:** Internally consistent snapshots and receipts are narrower than an independently observed execution or complete historical filesystem/process reconstruction
- **U:** No new GPU/model observation, numerical precision success, timing/speedup, semantic/task quality, GUI authority, cross-device generalization, runtime adoption, or product claim. V5's separate result and all earlier STOP/FAIL/HOLD dispositions remain unchanged

Final-head CI and merge verification remain separate integration gates. This note does not certify an unobserved merge or change the consumed-allocation/no-retry boundary.
