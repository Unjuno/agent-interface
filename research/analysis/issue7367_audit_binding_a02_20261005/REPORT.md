# A02 result — frozen workload binding

## H / T / D / C / U

**H.** The A01 auditor can accept a changed post-freeze workload if RAW's self-reported workload and canonical record digests are updated consistently, because A01 checks RAW against current workload bytes but not current bytes against PRE-RUN's frozen workload digest.

**T.** Preserve A01 unchanged. On throwaway copies, mutate a dead record payload and update the corresponding RAW self-reported digests. Demonstrate legacy auditor acceptance. Implement a versioned read-only successor auditor that additionally verifies workload bytes against PRE-RUN and independently checks frozen continuation uses. Test the unchanged and mutated bundles. Then invoke the successor once on the retained RAW; never rerun the candidate.

**D.** PASS only if legacy control reproduces acceptance, the new auditor passes the exact retained bytes, and rejects the self-consistent mutation as `FAIL_FREEZE_BINDING` with the frozen workload comparison false.

**C.** A broader change to the A01 auditor could be simpler, but would mutate historical evidence. A02 instead adds a separately versioned auditor; independent source review is still useful.

**U.** This proves binding for the retained synthetic A01 bytes, not general audit-system correctness or graph completeness. Host-native formal audit does not repeat or validate A01's container execution claims.

## Result

**PASS_RETAINED_BYTES_SCOPED.** All 9 formal checks passed on the retained A01 bundle. In particular, the actual workload SHA-256 equals PRE-RUN's frozen `37263f1731de25e71285bf1fc3527935380ef1ea315949df4985da1eebd3cc09`; A01 run/auditor source hashes match; every frozen continuation use remains selected; the selected set matches the independent continuation oracle; evicted IDs are outside the required set; and every canonical record digest matches RAW.

Construction tests: 3/3 passed. The legacy auditor accepted the self-consistent post-freeze mutation control. A02 accepted exact retained bytes and rejected that control as `FAIL_FREEZE_BINDING`. This is the concrete gap noted in review on PR #7515, reproduced without changing A01 or rerunning the candidate.

Formal command: `python -B audit_v2.py --root source --raw source/container-out/RAW.json` (CPython 3.12.10; exit 0). The exact JSON stdout is in `formal-audit.stdout.json`.

The original A01 PASS remains untouched and scoped to its finite synthetic declared workflow. A02 only strengthens byte provenance; it does not broaden A01's claim.
