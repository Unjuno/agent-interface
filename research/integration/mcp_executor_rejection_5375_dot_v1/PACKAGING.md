# Lossless module-map transport

This publication preserves the original first failure in Issue #5539, successor to #5375. It changes no logical study bytes and grants no rerun. The original full module, harness, oracle, raw responses, controls, warning stderr and FAIL receipt remain directly readable.

The original logical package has 77 files / 655,302 bytes. Seventy-five are direct files. Only two large JSON module inventories, `preflight-01/RESULT.json` and `formal-01/LOADED_MODULES.json`, are stored as lossless regular-file ZIP members in `MODULE_MAPS.zip.base64`. Their original logical bytes total 305,670. Exact decoded/encoded sizes and SHA256 identities are in TRANSPORT_MANIFEST.json; the encoded transport is 88,029 bytes including its final LF.

The transport manifest maps all 77 original paths to direct storage or exact archive members with logical size, SHA256 and Git-object identity. ZIP entries are sorted, regular 0644 files, with fixed 1980 timestamps. No source/executable, symlink or directory entry is archived. Existing verified Git objects can be reused for the 22 upstream source/test copies.

The original MANIFEST, FREEZE, source-before/after and output receipts remain byte-identical. They describe the restored logical layout. They are not a claim that the two archived members are separately present in the checkout. Absolute host/module paths in the original receipts describe the measured environment; restoration proves logical bytes, not that another machine has the same installed dependencies.

## Restore bytes only

Run `python -S -B restore_data.py /absolute/path/to/a-new-directory`. The destination must not exist. The helper validates the entire archive/direct map before destination creation, rejects duplicate/unsafe/unexpected members or nonregular types, and writes files exclusively. Use a trusted, nonconcurrently-mutated parent directory. The helper never imports or executes the retained MCP, harness or auditor.

After restoration, independently inspect REPORT.md and verify the original 76-entry MANIFEST, 49-entry FREEZE and output RECEIPT. Do not execute run_once.py or repeat the consumed executor-fault allocation during restoration or CI.

Publication construction note: the first packaging command's console-only `zip_bytes` diagnostic was affected by a reused loop variable. The encoded/decoded hashes and sizes stored in TRANSPORT_MANIFEST were calculated before that loop and are authoritative; subsequent independent decode/hash review verifies them. No original artifact, archive member or recorded scientific outcome changed.
