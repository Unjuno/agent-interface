# Current-source empty-event compaction compatibility (#8244)

Prospective source publication, 2026-10-06. Formal invocations: zero at this commit.

Base main: a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028. Exact complete upstream module blob: 662a3fc596e9aa3de171ab2f3486fac07ac17dd3. The proposal adds only the retained four-line empty-index return after strict JSON encoding. No previous timing allocation is repeated or represented as new data.

## H/T/D/C/U

H: preserve exact current-module output, input nonmutation, reference selection and error boundaries on finite acyclic JSON trees with string keys. T: 96 fixed input rows (depth 0/2/8, dict/list nesting, four event contexts, both report_refs values, both raw-report equality cases), two module calls per row; separate raw-only auditor and eight effective mutations. D: byte parity, exact independent reconstruction, source/process integrity and all 12 targeted tests required. C: unchanged implementation may be preferable if maintenance cost exceeds the small historical local saving. U: no full CLI/MCP/backend, native input, model/task/token/latency or cross-platform claim. Same-author separate audit is not nonauthor review.

The four source-XX.bin files concatenate in manifest order to a literal TAR.XZ archive. SOURCE_MANIFEST.json binds all chunks and the complete archive. It retains all 17 source/freeze/construction files including the 96 exact inputs, full old/new modules, runner, raw-only auditor, controls, tests, proof/protocol and actual red/green logs. Extract only regular relative files into a NEW private destination after verifying all hashes. Frozen PROTOCOL.md and FREEZE.json inside the archive are authoritative. Exact FREEZE SHA256: 92bbb0e0f01bb4da09d15e0e628cf1cb2838c6d27b9ab2ec46ac6bb94527f5e0.

Execution after exact public readback: python -S -B execute.py, once, then separate audit.py and controls.py invocations. execute.py observes its direct child's actual wait status and bounds it at 20 seconds. No repeated old timing/GUI run. No shared workstation/GPU/game lane is used; supplied Linux x86_64/CPython3.13.5 private container only, without Docker/WSLc/OrbStack image attestation.

Construction: unchanged module has 11 passing tests plus one expected encoding-count failure (4 instead of 1); proposal passes 12/12. A packaging exporter bytes/string TypeError was corrected before formal; no frozen source or outcome changed. Publication incidents remain under #8244, not new research Issues.

Roadmap: public source readback -> one differential run -> raw audit/controls -> complete evidence and focused proposal PR -> exact-head checks/nonauthor review -> merge only when gates permit. No self-approval or main mutation is authorized by this source publication. #3544/#57/#59 and global ROADMAP remain open.
