# #1615 Multimodal substrate projection roundtrip A2

Measurement-only successor to retained #1602 integrity stop.

H: #1602 candidate/oracle semantics pass the original safety gates when omission accounting requires actual before/after mutation and stale-version/ABA counters are separated.
T: exact reused candidate/oracle/baseline; same seed 159620260918001; same 120,000 traces and six 20,000-row strata; one formal invocation; predecessor corpus/result-stream digests must reproduce exactly.
D: candidate/oracle mismatch0; projection mutation0; omission mutation0; conflict overwrite0; old-version mutation0; compaction change0; stale20k; ABA20k; forged120k; cross20k; expired20k; valid revalidation40k; unsafe baseline >0; exact predecessor corpus/result-stream digests; audit pass.
C: measurement repair does not establish real model compaction/storage/runtime behavior.
U: synthetic semantics only; reruns/replacements/tuning0.
