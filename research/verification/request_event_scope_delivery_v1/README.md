# Request-event scope: retained 36-case experiment (#4042)

**Evidence delivery only.** `PASS_REQUEST_EVENT_SCOPE_SCOPED` does not qualify a
production runtime, a GUI task, causality, or permission to retry an operation.

This directory retrospectively publishes the already executed allocation
`request-effect-scope-20260922-01`. The original local source freeze was
2026-09-21T20:05:31.259543Z; Issue #4042 was created after execution. There is
**no claim of GitHub preregistration** and no new formal execution in this
publication continuation. Historical publication-STOP statements remain verbatim
inside the retained files; this README records the subsequent delivery.

## Result

| Measurement | Retained count |
|---|---:|
| Fresh SQLite cases (12 conditions, 3 repetitions) | 36 |
| Actual application and read-only observer children | 72 |
| State-only exact-value PASS | 33 |
| Own single committed event plus current value match | 9 |
| Unsupported naive completion: contradicted / unknown | 18 / 6 |
| New consumer's unsupported completion | 0 |
| Independent raw-audit errors | 0 |
| Semantic corruption controls rejected | 15 / 15 |

The naive comparator is explicitly authored for this experiment. The previous
value-only verifier is unchanged and does not itself claim request execution.
The new consumer receives a stronger event contract, so this is not an
equal-information efficiency comparison. `UNKNOWN` is not execution failure.

## Inspect and re-audit without an experiment

The eight `evidence-*.b64` parts reconstruct a hash-bound XZ/USTAR archive of
**all 110 original research files, 1,594,009 content bytes**. It includes every
source, the 36 formal databases and raw process records, excluded construction,
local freeze, original reports/audits and retained failure records. `PACK.meta.b64` (losslessly encoded JSON manifest)
binds each part and every original member. No binary/model/runner is executed by
`unpack.py`; it rejects existing output, unsafe paths, non-regular archive entries,
wrong counts/sizes/hashes and over-limit archives.

Use a fresh directory under a trusted existing parent; do not use Python `-O`.
From this published directory:

```sh
python -I -S -B unpack.py /tmp/request-event-review-4042
cd /tmp/request-event-review-4042/research/verification/request_effect_scope_34_20260922_v1
sha256sum -c SHA256SUMS
python -B -S -m unittest -v test_binding
python -B -S audit.py formal-01/data --report /tmp/request-event-audit-4042.json --controls
cmp formal-01/AUDIT.json /tmp/request-event-audit-4042.json
```

Do not run `execute.py` or `runner.py` with the consumed allocation. Any genuinely
new experiment needs a new prospectively frozen allocation, not a retry of these
rows. The original 90-condition exact-value study is owned by #4007 and is not
republished here; its exact verifier dependency is included in this study.

`binding.py` and `audit.py` are directly readable copies for code review. Their
complete runnable context is in the restored tree. `PREREG.md`, `FREEZE.json` and
`AUDIT.json` are unchanged copies; `PUBLICATION_CHECK.json` records the new
read-only checks. `REPORT.md` states the integration boundary and limitations.

## Provenance

- Original preformal main: `1c817de45cf944d144d76e288823b63bc0ec73a4`.
- Publication intake main: `e4c2e58122aa138e421048d8e86ec18259143b9e`.
- Formal raw SHA256: `b9b9c26c21284c153193ac352b8315b89485f340858c597246d1c706e32f9180`.
- Original audit SHA256: `9b130e98abed8ca1c05a59cd15e9267f33813864b8535f468004fc7ef4dafcdb`.
- Compressed archive SHA256: `c1c9161545d108964c85f192a77dc849462394671c58afd086b2872e41e285ce`.

The outer conversation ZIP is not reconstructed by this capsule; its identity is
retained in `PACK.meta.b64` (losslessly encoded JSON manifest). All 110 original research members are reconstructed
byte-for-byte. Hashes bind bytes, not authenticated origin. Original local paths
and diagnostic timestamps are preserved as provenance, not deployment settings.
