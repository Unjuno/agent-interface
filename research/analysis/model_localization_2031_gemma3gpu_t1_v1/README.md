# Issue #2031 T1 evidence bundle

Read [REPORT.md](REPORT.md) for the scoped result and protocol deviation, then [FREEZE.md](FREEZE.md) for the H/T/D/C/U allocation. Byte-exact candidate calls and the independent diagnostic audit are stored under `research/analysis/model_localization_2031_gemma3gpu_t1_v1/formal/` in the repository branch. The prior #1968/#2173 result remains separate and unchanged.

**Artifact integrity hold:** 113 of 114 entries in `SHA256SUMS` match the SHA-256 of their committed Git-blob bytes. The `REPORT.md` entry does not: manifest `1bbd2132…abd90`, committed bytes `2b35b838…05437`. The contemporaneous source bytes matching the manifest value were not available in the inspected history. Do not regenerate or silently replace the historical report; treat its exact-byte binding as unresolved. The retained bundle is diagnostic evidence, not a fully hash-verified formal PASS.
