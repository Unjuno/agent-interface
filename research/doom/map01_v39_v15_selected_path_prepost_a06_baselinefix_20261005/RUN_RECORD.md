# A06 run record — trace sample audit passed

- Allocation: `V39-V15-PREPOST-A06-BASELINE-FIX-20261005-01`
- Candidate/runtime invocations: 0
- Auditor invocations: 1
- Retries: 0
- Auditor source SHA-256: `13a09f56278cc2d9ea91c022918d1c900756a0ab2749742c37b7fdf62b13f051`
- Freeze SHA-256: `a1e9b79a90302ae033eb020cb0c04d4519e15535f68f0344bb082e602bc7bca0`
- Runtime: WSLc, pinned Python image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; network disabled; one CPU
- Direct-mount preflight: 8/8 hashes matched
- Local construction tests: 3/3 passed, including all 52 raw baseline checks
- Formal launch UTC: `2026-10-05T09:05:08.8441940Z`
- Formal exit UTC: `2026-10-05T09:05:09.4049823Z`
- Container exit: 0

The independent audit passed all 52 baseline checks and rejected all 12 mutation controls. It verified that each retained pre/post `keymap_sample_result` matches its named `query_keymap`, expected stage, summary sample, and ordering around key-up attempts. The previously observed A05 mismatch was a validator expectation defect; A06 uses the raw-backed normal pre-sample `[65, 74]` and the retained query and result agree.

Result SHA-256: `5b9634db26fb3e059d84f3a2191c856207a8930a1f0034a61dc8dfda587f349c`. Empty stderr SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Exit file SHA-256: `5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9`. Pre-run context SHA-256: `d1d4cd5da4ca1d8395603424fc506ba29540070633fa372acbb564a85a07c13d`. Start/end timestamp SHA-256 values are recorded with the files.

This is a scoped audit-integrity result over immutable synthetic fake-X output. It does not establish real X11 or physical keyboard state, application effect, useful feedback, latency, recovery efficacy, live threat response, gameplay, or safety. A02 remains FAIL, A03 remains its earlier scoped result, and A04/A05 remain terminal failures. No candidate was rerun.
