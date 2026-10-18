# A04 pre-freeze construction probes

C01, C02 and C03 are separate unallocated functions.exec V8 construction probes, each with one candidate and one auditor call. They are not formal allocations or retries. Compact summaries and failing auditor sources are retained; the in-memory construction row tables were not serialized. Full row-level evidence is retained for formal A04.

## C01

2,600 rows; candidate effects 2.583333333333349 and 0.16666666666666777; candidate U=1 distal 9.443750000000001. Auditor base_audit=false because it compared distal numeric objects by exact JSON serialization against 9.44375; all 16/16 mutations were rejected. This was a floating-point assertion defect, not a method FAIL. Auditor/fixture/summary blobs: c5bda42b98dc0ae3005673d736c04f7f7ce06c71, e4bc2f753e10582706401c180523dda3e6b80b1c, 875440964b889315e149939f56d59587d6e8eb7b.

## C02

After numeric tolerance and a missing-window control were added, base_audit=true but only 13/17 mutations were rejected. The row-mutation validator reused its baseline comparison for mutated copies, falsely accepting four row alterations. Auditor/summary blobs: 4f1433d4ea6c8c43c5133208f0c1771af2efd89b, a5c65cb4986a6e484d8d9bc0b1ceecef8cffcb1c.

## C03

The final validator compares every mutated row multiset against the independently reconstructed expected set; base audit true, 17/17 rejected. Summary blob: 3b4ac9e2bf010df33ebfa06fe797b67ff083eb0c.