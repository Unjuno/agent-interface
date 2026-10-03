# Issue #6003 / PR #6042 archival qualification

Dated 2026-10-02. This is a mechanical preservation and navigation repair, not a new experiment or a scientific promotion.

## Scope and owner gate

The seven original files in this directory are retained byte-for-byte from PR #6042 head `7ebeff330b39d2e1836168c4201cad0221f51be0`. The recorded result remains `PASS_HOST_ONLY_CONSTRUCTION`: one Windows-host candidate and one separate auditor, Python 3.11.9, with no Docker/WSL, GPU, model, GUI, or empirical result. The disposable-container condition remains unmet. No original source, freeze, report, raw output, or audit output is changed by this repair.

[Issue result comment 5931505537](https://github.com/Unjuno/agent-interface/issues/6003#issuecomment-5931505537) keeps PR #6042 Draft pending an environment-compliant follow-on or explicit decision on the container condition; [comment 5931636486](https://github.com/Unjuno/agent-interface/issues/6003#issuecomment-5931636486) retains that gate. This repair does not supply that decision, authorize a successor allocation, promote the PR, or close the Issue. Candidate/auditor execution is not repeated.

## Digest transcription qualification

The historical REPORT.md prints the auditor-source digest as `e1bf0aca36389439bcf693ed775ff038e297d7c0c6d4e5f27fab5916a46d4b2`, which has 63 hexadecimal characters and cannot be a complete SHA-256 digest. The report remains unchanged.

Exact Git blob readback of audit.py instead yields `e1bf0aca36389439bcbf693ed775ff038e297d7c0c6d4e5f27fab5916a46d4b2` (64 characters), matching the `auditor_sha256` field in the retained independent_audit.json. This is a byte-identity observation, not a rerun or a retroactive upgrade of the original result.

## Original-file identities

These seven blobs total 24,831 bytes. Candidate and independent audit JSON retain their original CRLF bytes; no newline normalization is allowed. The existing narrow `-text -whitespace` rules for those two files are retained additively alongside current-main attributes.

| Original file | Bytes | Git blob | SHA-256 |
|---|---:|---|---|
| FREEZE.json | 4658 | `0a63735f9456690a41493db9d05ab77b5764964f` | `8ff6c4d5d1594ab4623c52483b0f033a8aa6b5ede7f74ea71809461a9469352b` |
| METHOD.md | 2986 | `e7cb6ce22444d7d1c9b303ab428d2fa07f582d72` | `c1d8e911647f6d31cec57409d2d511e803420921b41dcf97b83ece1fe4e5293d` |
| REPORT.md | 2717 | `c1396b119832285c2e20b9830c2ddce5565c42f4` | `4b759bd38edb5423b5a50f57cbe99e4c47a59b9559bc47e76e455c29aeb9871d` |
| audit.py | 7345 | `b17a46552b74e647daa12efa43dee4e46ea79278` | `e1bf0aca36389439bcbf693ed775ff038e297d7c0c6d4e5f27fab5916a46d4b2` |
| candidate_result.json | 2926 | `fc9c7eec21e124d226243b2b8b22d3ad7768acd5` | `0a267821274056f87a3c6beace29b50623865382c2fe4dda0d0bba9e150af57b` |
| independent_audit.json | 589 | `559359227a55527d6d22d66a46a7910ec58baea4` | `9a5e32bf1a1e76437d9989e886c263223b35625f77ee0d5ee6e59a9c1f3b78c9` |
| select.py | 3610 | `cc9c0feb91c139729527bcdf59cd31e06c1ecf77` | `f23ce27bed6d9c6de6e29b5715e667783d552ecbd73b049a80fc3e2955e3a316` |

## Mechanical integration boundary

The repair reconciles the branch with main `9a327d0511f02c7b8ebd175e20f96a43028578ca`, preserves every current-main path, adds only this historical package and qualification, unions the generated analysis index, and keeps the PR Draft. It does not overwrite another allocation or alter a workflow.

The synchronization commit uses `[skip actions]` because moving this old branch forward introduces unrelated historical workflow paths in the push diff. Current-main and original-head workflow definitions were inspected: no `pull_request_target` or `workflow_run` trigger was present, while unrestricted path-filtered push workflows can execute research candidates. The skip contains that automatic-execution risk; it is not a passing CI result. New-head CI remains unverified and all owner/review/check gates remain in force.
