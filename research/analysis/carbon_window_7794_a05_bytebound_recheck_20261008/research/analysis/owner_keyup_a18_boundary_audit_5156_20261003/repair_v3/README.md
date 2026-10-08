# Revision 3: type-sensitive parsed JSON witness joins

Independent review [5964217806](https://github.com/Unjuno/agent-interface/pull/6865#issuecomment-5964217806)
confirmed the original positive and all fifteen v2 teardown negatives against
its separate retained raw-only oracle. It then exposed two new type-alias cases:
an appended `verified=1` versus Boolean true, and cancellation's final witness
`verified=1` versus Boolean true. V2 accepted both because Python dict equality
equates those values. This qualifies the v2 exact-witness wording; it does not
falsify original A18 live data or relabel the earlier C01/v2 denominators.

`json_witness_audit.py` composes with unchanged v1/v2 checks and compares sorted,
compact JSON serializations of receipt projections and recorded witnesses.
Boolean, integer and floating values have distinct encodings; object key order
is ignored. Non-JSON/nonfinite serialization fails closed. This is a small
stdlib comparison for parsed JSON, not a general schema or authentication system.

Ordinary native Windows 11 / CPython 3.12.10 regression covers one method and
38 subcases: the previous 30, the two reviewer negatives, five related Boolean /
number type aliases, and a positive reordered-object control. V2 produced seven
failed subcases; v3 matches all 38 (two positives, 36 negatives). Original red
source, actual UTC/exit receipts, logs and source hashes are retained under
`verification/`. Only the private absolute package prefix in the red traceback
is replaced with `<package>`; the original stderr is retained privately and its
digest is in the red receipt. This ordinary regression ran no formal wrapper,
candidate, backend, container, GPU, model, X11 or input process.

The historical C01 45-file manifest, ten frozen inputs and v2 program/test/output/
manifest bytes remain unchanged. The current navigation README is updated; its
old v2 bytes are retained exactly in `retained-entry-v2.md` and at original head
`f0ca86d295265f7ee55da2d4805b5ab471944d3a`. When checking the historical v2
manifest in this revision, resolve its `README.md` entry to that retained copy.
`verification/history-readback.json` records that explicit mapping and all hashes.
`../REVISION3-SHA256SUMS.txt` separately covers current navigation and v3 files.

Use this v3 entry point for the proposed fixed-A18 JSON consistency check;
keep prior programs for reproduction of their historical results. Coordinated
fabrication, duplicate-key rejection during initial JSON parsing, authenticated
backend provenance, arbitrary Python objects/schemas, physical input, application
effects, useful feedback, MAP01 efficacy, thread safety and performance remain
outside the verified scope. No exact original JSON byte equality is claimed:
the comparison is of parsed values/types after removing only caller timing keys.
Existing Windows workspace failures remain disclosed in `../CI.md`.

From the package directory:

```sh
python -B -m unittest -v repair_v3.test_json_witness_audit
```

This proposes a research audit supplement. New content approval, current-main
combined-tree verification and conditional application remain separate. No
runtime, workflow, historical live record or formal allocation was modified.
