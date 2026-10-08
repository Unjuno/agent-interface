# Persistent receipt file experiment

The previous delivery-cost experiment included repeated filesystem open/close.
This experiment isolates that cost using the same 15 frozen flush receipts from
actual assistant cohort delivery-self-use-02, totaling 11,758 bytes.

`receipt_journal.py` accepts an owned binary stream, writes one JSON line and
flushes for every append. The caller opens the file once and closes it in finally.
It counts a record confirmed only after full write and successful flush. Write,
short-write or flush failure makes the journal unavailable for further appends.
Serialization errors occur before touching the stream. Close is idempotent; close
errors propagate. It is single-writer and does not supply synchronization.

Twenty blocks alternate reopen/persistent and persistent/reopen on the same WSL
Windows-mounted repository filesystem. Both paths serialize identical records,
write identical bytes and flush each record; the timed region includes opening,
all appends/flushes and final close. Temporary directory creation and output
verification are excluded. Raw block measurements and source hashes are in
`results/receipt-journal-01`.

| Receipt persistence metric | Reopen per record | Persistent file |
|---|---:|---:|
| Median time for 15 records | 92.125 ms | 7.424 ms |
| Output bytes | 11,758 | 11,758 |

Persistent is faster in 20/20 blocks. Median paired difference is -84.851 ms;
range -128.413 to -60.139 ms. This supports eliminating repeated open/close on this
filesystem, not a general model/GUI speedup. It does not compare batching, async
logging, fsync durability, slow terminal output, lock contention or other disks.
No live runtime entrypoint has changed yet.

Injected write failure, partial write and flush failure all leave confirmed=0,
propagate the original exception and reject subsequent appends without further
stream mutation. Append-after-close is rejected and repeated close is harmless.
Partial/flush failure may already leave bytes in a file; failed is not rollback.
Flush means Python stream flushing, not stable storage or model delivery.

Next integrate the owned stream into an experimental entrypoint with explicit
teardown and output-failure tests while input is held. The runtime must still
release independently when I/O blocks. A synchronous persistent stream can block;
this benchmark supplies no new release guarantee. Keep previous failure cohorts
and qualify this change separately from bounded observation-reference retention.
