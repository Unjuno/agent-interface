# Issue #4055 — preserve partial receive progress alongside errors

**PASS_NATIVE_BATCH_PREFIX_ERROR_BOUNDARY_SCOPED**, research-only. Legacy policy remains **FAIL_UNREPORTED_CONSUMED_PREFIX**. Full H/T/D/C/U, construction STOP, conditional argument and limits are in [REPORT.md](REPORT.md); public premeasurement source hashes are in [PREMEASUREMENT.md](PREMEASUREMENT.md).

The exact old C/Python receiver and the new partial-result variant are directly readable here. The complete new corpus (64 files /4,189,310 bytes), including all48 raw cases and every source/binary/process/construction/audit record, is retained losslessly in eight binary parts described by PACK.json. Original file bytes, including the disclosed protocol bytecode cache, are reproduced exactly. No measured data are regenerated.

| Result | Exact legacy | Prefix plus error |
|---|---:|---:|
| Fresh local socket cases |24|24|
| Native-written in-bounds datagrams |45|45|
| Exposed to caller |30|45|
| Consumed but unreported |15|0|
| Oversize errors |15|15|
| Unread after the two declared calls |3|3|

The test inputs are synthetic local datagrams, not current GUI observations. A zero-length datagram counts as one transport item, not a valid image or stream EOF. No model/input/replay authority, performance improvement or production adoption follows. The prior Xeon32-case performance HOLD remains unchanged; its complete a55fed37 ZIP is still separately conversation-hosted and is not claimed inside this bundle.

## Read-only verification

Use fresh output paths. These commands unpack data and audit retained evidence; they do not launch the consumed socket experiment or load its native binaries.

```sh
python -S -B unpack.py /tmp/issue4055-review
cd /tmp/issue4055-review
python -S -B audit.py . --out /tmp/issue4055-audit-new.json
cmp AUDIT.json /tmp/issue4055-audit-new.json
python -S -B controls.py . --formal --out /tmp/issue4055-controls-new.json
cmp CONTROLS.json /tmp/issue4055-controls-new.json
python -S -B -W error::ResourceWarning -m unittest -v test_audit
```

Expected audit SHA256:55012209b2fe02e57e84081e8be4af72f24386143483f56de307286e1dafd532. Expected capsule SHA256:1c0e9f51fa68f02456442d980ebb85f69d000c99cde2ee0b0fb82807a9b6e0ab. Checksums establish byte integrity, not publisher authenticity.

18 unit methods and14 copied-formal-data controls pass. Fresh restoration reproduces all64 files, the original audit and controls byte-for-byte;8 packaging refusal controls pass. See VALIDATION.json. This is a same-author independently implemented auditor, not external human review. Repository CI/merge status is recorded in the PR and is not inferred from local checks.

Only this additive research namespace is modified. #2117, #2789 and the broad roadmap are not closed or promoted by this finite transport study. Do not rerun the consumed invoke.py/run.py allocations.
