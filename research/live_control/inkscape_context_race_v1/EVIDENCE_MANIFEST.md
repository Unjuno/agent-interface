# Evidence retention boundary

GitHub retains the frozen study source, preregistration, schedule, preparation-failure record, REPORT, aggregate per-case results/audit/environment/corruption controls, and SHA-256/byte counts for all 40 measured PNG captures.

The exact full local archive contains 119 retained files and is attached to the conversation as `inkscape_context_race_v1_complete.tar.xz`:

- bytes: 1348360
- SHA-256: `7184ed8a643a1ceb8d32cbbb0c9ba56cfa38f19db885549326dcaf7491dc2649`

The 40 PNG capture bytes are **not claimed GitHub-retained**. Their exact SHA-256 values are in `RESULT_SUMMARY.json`. This boundary does not affect the persisted-SVG effect endpoint, but independent recomputation of the visual selection-marker pixel count requires the full local archive.

Fresh extraction of the full archive reproduced the frozen audit object byte-for-byte (audit stdout SHA-256 `98d902e8fc0973e879e85f806dc2534d3ba604b4e13b59c6a7b7d0670a62745a`).
