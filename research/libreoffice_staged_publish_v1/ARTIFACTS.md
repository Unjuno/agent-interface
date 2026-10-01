# Evidence retention boundary

This branch retains the final decision report, preregistration, compact audit and summary for Issue #299. The experimental BASE is `ed04bba63813ddfa508912eaaadcdca87d59600b`; historical/shared runtime files are unchanged.

Exact executed source SHA-256 values are recorded in `FINAL_AUDIT.json`. The complete curated conversation evidence bundle contains the executed sources, first harness failure, construction output, all rung result JSON/XLSX/log evidence, and a per-file manifest:

- `libreoffice_staged_publish_v1_evidence_final.zip`
- files including manifest: **121**
- bytes: **158,352**
- ZIP SHA-256: `c074531ee08897f64c5232330b5dbcc22df7d8929e0d8162a24f92639564a51a`
- embedded manifest SHA-256: `79220d6e7aeb439a7e05306e2706f9d1f06aa44772155008a2ec9a8b8b2e865a`

A deterministic local executed-source archive was also frozen:

- `libreoffice_staged_publish_v1_sources.tar.gz`
- bytes: **12,679**
- SHA-256: `7e68dcc9f24732cdc1831dbd0bcfa056900cd26ba8cacf8f19dfad20d6322531`
- Git blob SHA for those exact archive bytes: `13d13009e88160de832bbb2ecefc8461c704fdbf`

The binary archives themselves are **not attached to this GitHub tree**. An attempted binary connector staging produced a blob identity different from the locally frozen archive and was deliberately left orphaned/unreferenced rather than silently treated as evidence. Do not call this branch byte-complete raw retention.

Canonical GitHub discussion/freeze/result receipts are on Issue #299. The final scientific disposition is `FAIL_GENERAL_PATHNAME_COMMIT_BOUNDARY`; negative evidence is retained rather than tuned away.
