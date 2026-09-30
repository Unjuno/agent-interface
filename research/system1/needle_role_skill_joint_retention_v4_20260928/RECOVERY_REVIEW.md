# V4 construction FAIL: preservation and source-binding review

Recovery review date: 2026-09-30.

## Two separate dispositions

- Original observed-record disposition: **FAIL_ZERO_UPDATE_CONSTRUCTION_GATE**. Preserve the published 13-test / 12-pass / 1-failure result and all 13 original files unchanged
- Current source-binding disposition: **HOLD_EXACT_MOUNTED_SOURCE_RECONSTRUCTION**. Exact published Git contents have not been matched to the separately declared container-mounted source bytes

This is an additive preservation review of [PR #4948](https://github.com/Unjuno/agent-interface/pull/4948), head `c3866e94ce580503db1c4f96e57e245cfc9dbc03`, for [Issue #4941](https://github.com/Unjuno/agent-interface/issues/4941). The allocation remains `needle-role-skill-joint-retention-20260928-v4`. Recovery intake main was `cbca212667bc0c256184ef71bd8c1000d8c9a8aa`, where this original v4 directory was absent.

A source-provenance gap does not erase the retained failure, establish a new scientific failure, or turn the test into a PASS. No original hash, source, freeze, receipt, threshold, seed, or outcome has been edited to make the records agree.

## Independently verified retained bytes

Read-only GitHub retrieval and byte hashing recreate all 13 original Git blob IDs exactly. The nine source/document blob IDs declared by `FREEZE.json` match the published objects; the seven executable-source IDs also match `RUN.json`.

Decoding the original `evidence/stage0_01/RAW_STDERR_BASE64.txt` yields exactly 2,980 bytes with 28 CRLF line endings and SHA-256 `04eb157f6e5689b3312d6985d37efd6aaa0c4e7e746dad46be874d400083e850`, matching `RUN.json`. Static text inspection finds 12 `ok` test lines, one `FAIL` test line, `Ran 13 tests in 0.474s`, and `FAILED (failures=1)`. The failed-test name and two displayed cross-entropy values agree with the receipt. These are descriptions of the preserved test output; no current test, timing measurement, numerical comparison experiment or inference was run.

The receipt records empty stdout, exit 1, one invocation, no retry, no optimizer step, no construction-seed run, and no formal fit. The stderr bytes are independently available; the process exit, orchestration accounting, image-tag/digest binding and isolation claims remain historical receipt claims, not a new independently observed container execution.

## Unresolved mounted-source identity

The exact committed source bytes have the SHA-256 values below. None matches the corresponding `FREEZE.json` mounted-file declaration; the seven executable-file declarations in `RUN.json` agree with the freeze's mounted-file declarations, but still differ from the published Git contents.

| File | Exact published Git-content SHA-256 | Declared mounted-file SHA-256 |
| --- | --- | --- |
| `runner.py` | `e72febb498840ec20fc30068c192fec58ce8b854a0e9b2c1c8407e63e9df5619` | `79a42ce467945eef306f714b5d63347700f83032241480940b65c56ee97b2c26` |
| `audit.py` | `0d76180bc6de0018fba4f8093045bab5c9d3fdbd462de49ba6296607c35ea8ca` | `7740e2e8b27810d1cf9a9d05c4565def0934170cb17f8af4e63af8790e7b4c96` |
| `test_construction.py` | `b2fbc00a85a2fec9afa64aaa8f31d00eb3c0089d7446b364688a32ed1e3c8e0e` | `597b02c53eac267412464520845af143f3c483984e30762618f1cae198f452b7` |
| `construction.py` | `1d83bae22b54a2f8c24d99705f4bcb47b0c5e0c76d8dd893dbef91f4bf8c295e` | `7dd4c3e32f5d994772041e4d8b7aaadf806cc060a672af867adbf37ae9aa297d` |
| `construction_audit.py` | `cc85b78e99933c22077e710eb88f20d8d3d565d0d6dd1caec2dd9430fadd35bd` | `04c865eddd6c1e61627b59ac064027e480adb0cdb9dbd0e2ddf66faff439ddca` |
| `construction_launcher.py` | `3615a7f4e96f8a1575cfa7046efeb42f5a4f47ced1d3b6d102c85aa4cb0c42c8` | `d528a868f73ae88a4363b0960055565a8f46f7218e70992b68ecad0c84f32c9f` |
| `test_launcher_boundary.py` | `46cad774d6df59542060110754d35a0fb481830ffde2b7d3955fb85f8a2d0853` | `28616a26e9b87c45ba9acd23e4338964e64411d58a91083ffacd0bd3b49ff87c` |
| `CONSTRUCTION_BOUNDARY.md` | `2cccadca5c920567c08dff50a741386916d50b0f770160ea5dc3a891718f8745` | `cc289bce5db333e7b562c5b50bd357b7ed8c2b821c66a7876c3e66922ad8015b` |
| `README.md` | `23e024db362224e77b94457b0ef5496686dcd9a4d2b3ec364d6374bc8aa09d12` | `a58f7ae160a248c532e6be833d58bcee7f21840d0629d9b604ea3953248a9a05` |

Two separately recorded identities are not a verified mapping between them. The retained traceback and assertion text do not substitute for recovering the bytes that match the declared mounted hashes. No speculative normalization, generated replacement source, or changed manifest is part of this publication. This review does not claim that the original mounted bytes are corrupt or that the retained stderr is fabricated; it identifies the unresolved source-to-execution binding.

To clear this specific HOLD, recover the original nine mounted files or a complete lossless artifact containing them, verify every declared mounted SHA-256, retain their original identities additively, and document their relationship to the already-published Git objects. Re-running the consumed v4 allocation, editing the frozen hashes, or substituting a later source version is not a recovery of the original evidence.

## Existing successor work was checked

[Issue #4949](https://github.com/Unjuno/agent-interface/issues/4949) explicitly preserves #4941/#4948 and preregisters a 1e-6 scalar tolerance under a distinct v5 allocation. Its [merged PR #4951](https://github.com/Unjuno/agent-interface/pull/4951) publishes 62 files under the v5 path, including separate construction/formal evidence, with its own audit-integrity HOLD and comparative-threshold miss. It is an existing successor, not a correction to v4's historical bytes or outcome.

[Issue #5081](https://github.com/Unjuno/agent-interface/issues/5081) and [PR #5226](https://github.com/Unjuno/agent-interface/pull/5226) describe distinct v6 source/audit preparation with separate resource and formal gates. Neither the inspected linked issue/PR text nor the complete v5/v6 changed-path inventories supplied a v4 mounted-source recovery artifact. The exact v4 allocation/path searches also found no such published recovery. This is the boundary of the search, not a claim that no original artifact can exist elsewhere.

Do not duplicate those allocations, borrow their passing construction results, or retroactively apply v5's tolerance to reclassify v4.

## H / T / D / C / U

- **H:** Published v4 source objects and the original failure stderr can be retained with an explicit, testable source-binding gap
- **T:** Recompute original Git blob identities, decode and hash retained stderr, inspect its recorded test counts, compare all declared source/mount hashes, and inspect linked successor evidence without executing repository code
- **D:** Preserve FAIL_ZERO_UPDATE_CONSTRUCTION_GATE; retain HOLD_EXACT_MOUNTED_SOURCE_RECONSTRUCTION until the exact original mounted bytes are recovered and checked
- **C:** Correct Git-object retrieval and internally consistent stderr/receipt fields do not prove that the container executed those exact published source bytes
- **U:** No new model/GPU/container run, numerical-quality conclusion, role-LoRA generalization, online-learning capability, latency benefit, runtime adoption, task benefit or product claim. Prior and successor FAIL/HOLD/STOP outcomes remain separate and unchanged

No source program, test, auditor, model, container, GUI action or workflow was executed for this preservation review. Final-head CI, independent review and merged-byte readback remain separate integration gates.
