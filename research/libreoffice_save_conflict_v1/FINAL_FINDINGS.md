# Final discrimination — metadata precision and mtime-restored stale overwrite

This file extends the retained pair-02/pair-03 report without rewriting those first outcomes.

## c254-pair-04 — timestamp metadata only

Frozen order: stable then touch; one arm each. Runner SHA-256 `da9a9ec2156457c96ab7f527eb4281d2f1688fc7271603e1c4aba3c32fc2751b`.

After the same final precheck, the touch arm changed no XLSX bytes, inode or file size. It only advanced file mtime via `os.utime` (Linux ctime changed as a consequence). The pre/post XLSX SHA remained exactly `307e9007cdd4cd44ed1abd3a32b14bf2c3dd407e2d2c49a726ec8681df32869a`, inode remained `1314135` and size remained 4,839 bytes.

LibreOffice emitted `Document Has Been Changed by Others` after the known `Confirm File Format` step and preserved the original `seed / old` file rather than saving the in-memory `office / preview` edit.

Disposition: **semantic false stop under the authored fixture ground truth**. Native conflict detection is broader than semantic content change.

Independent audit: zero errors; four deliberate corruptions rejected.

## c254-pair-05 — ctime/mode change with mtime fixed

Frozen order: stable then chmod; one arm each. Runner SHA-256 `faf9ba24048a15436c2d015da44c9f244d119111a2c7894ebaefb3f9544cfd64`.

The chmod arm preserved bytes, inode, size and mtime exactly while toggling the user-execute permission bit (`0644 -> 0744`), changing mode and Linux ctime. No `Document Has Been Changed by Others` appeared. Calc saved `office / preview` normally.

Disposition: arbitrary ctime/mode change is not sufficient to explain pair-04. The result is consistent with mtime being an important conflict signal in this fixture.

Independent audit: zero errors; four deliberate corruptions rejected.

## c254-pair-06 — relevant external content change with plan-time mtime restored

Frozen order: stable then restoremtime; one arm each. Runner SHA-256 `06cf992147449f5adac11adcf017ba2da065795d082d16938ff0d579118b9d7f`.

The external writer performed a relevant same-inode XLSX content rewrite, fsynced it, then restored the task file mtime exactly to the precheck value before Ctrl+S.

Evidence before save:
- inode stayed `1315152`;
- precheck mtime = post-mutation mtime = `1789503456461000888` ns;
- XLSX content changed from SHA-256 `94abac527f1a5b5b366494ce419b7b39108586cd270721851b4079b0806ce7f5` to external SHA-256 `5c1a8d5554689066335699faf6676977dd79bf96bba05ce64be85197ac01a0e9`;
- external workbook contained `A1=external`, `A2=replacement`, `A3=external-marker`, `B1=writer`;
- ctime and size differed, so not every metadata signal was hidden.

Result: Ctrl+S produced only the historical `Confirm File Format`. After that exact dialog was acknowledged, **no conflict prompt appeared**. Calc saved the stale in-memory plan, replacing the external workbook. Final durable XLSX SHA-256 `a178cd08904e33902d66a177a1b01588a3d0e5623b1709a14aad7d8d138764eb`; independent scorer recovered `A1=office`, `A2=preview`.

Disposition: **stale overwrite counterexample**. Under this exact LibreOffice 25.2.3.2/local-XLSX fixture, restoring plan-time mtime bypassed the native conflict response even though relevant external content, ctime and file size changed.

Independent audit: zero errors; four deliberate corruptions rejected.

## Corrected architecture conclusion

The native LibreOffice save-conflict mechanism is useful evidence but is **not equivalent to an authoritative effect-owner validation boundary**:

- pair-02: pathname replacement -> conflict prompt, external file preserved;
- pair-03: same-inode content rewrite -> conflict prompt, external file preserved;
- pair-04: content unchanged, mtime changed -> conflict prompt / semantic false stop;
- pair-05: mode/ctime changed, mtime unchanged -> no conflict, save proceeds;
- pair-06: content changed, mtime restored -> **no conflict, stale overwrite**.

This pattern is consistent with an mtime-centered or mtime-dependent detector, but it does not prove LibreOffice's internal implementation.

For Agent Interface, native GUI conflict prompts may be treated as additional evidence, not as a substitute for the plan-bound `context incarnation + semantic predicate` commit boundary retained in PR #251.

## Evidence boundary

Pair-04/05/06 full decision evidence remains in the conversation artifact. GitHub retains this decision summary and source hashes; the branch is intentionally not called byte-complete.

Curated decision bundle `c254_decision_evidence_v3.zip`: 126,550 bytes; SHA-256 `ace3525f28c969dac349c40d3242d7efe9067e670bceac3427c99ca04675b619`.
