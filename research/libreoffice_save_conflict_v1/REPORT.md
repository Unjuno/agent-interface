# LibreOffice delayed-save conflict boundary v1

Status: **RETAIN native conflict/refusal evidence for this LibreOffice/X11 fixture; HOLD general GUI promotion.**

Issue: #254. Immutable experiment BASE: `9088adefb48b97b79828774dd954bb8161885d59`.

## Question

After a final GUI/file precheck but before Calc's save effect, if the XLSX path is externally replaced with a different valid workbook, does LibreOffice silently overwrite the newer file or surface a native conflict boundary?

## Source/environment identity

- LibreOffice 25.2.3.2
- openpyxl 3.1.5
- retained X11 backend Git blob `b4f8e043ce4f8929d446e038418ea0fd3655bab0`
- retained Office X11 policy Git blob `3aeca10f62fb1366bcdd5fad561509cfcc0d91ab`
- c254-pair-02 runner SHA-256 `f15e57af4fa75a237e4333fee1f6a7763c2f29f979834f838534e758ff2a1a38`
- independent scorer SHA-256 `cb22bd2ab6f55c5c99a9135417b511d683fc519b193c809dedefe6ed23e6cc7a`

Private Xvfb/Openbox/profile and disposable XLSX only; no model, user file, network service, or historical allocation rerun.

## Retained setup/failure history

An unscored stable calibration identified the retained XLSX dialog title exactly as `Confirm File Format`. The scored allocation was frozen to dismiss only that exact historical format dialog; any other new modal remains untouched.

`c254-pair-01` is a retained HARNESS FAIL with zero scored arms: the parent runner did not propagate its private `XAUTHORITY` before its own Xlib calls. `c254-pair-02` changed only that environment propagation and allocation/output names. No rows are pooled.

## c254-pair-02 first complete pair

Frozen order: stable then replacement; one arm each.

Both arms open a generated XLSX (`A1=seed`, `A2=old`) and perform the retained fixture-bound edit to in-memory Calc state (`A1=office`, `A2=preview`). Immediately before Ctrl+S, the runner records focus/window identity plus file SHA/stat/inode.

Replacement arm then creates a separate valid workbook (`A1=external`, `A2=replacement`, `A3=external-marker`, `B1=writer`) and performs exactly one `os.replace()` on the task path before the identical save command.

| Arm | Durable outcome | Modal after Ctrl+S | Modal after known format confirmation | Release |
|---|---|---|---|---|
| stable | `A1=office`, `A2=preview`; 6,012 bytes | `Confirm File Format` | none | empty/verified |
| replacement | external workbook preserved byte-for-byte | `Confirm File Format` | `Document Has Been Changed by Others` | empty/verified |

Replacement details:
- precheck inode `1314174`, SHA-256 `2f8963f8...`;
- after `os.replace`: inode `1314297`, SHA-256 `50fdd687...`;
- after save attempt and native conflict prompt: same inode/hash `1314297` / `50fdd687...`;
- independent scorer while Calc remained alive recovered exactly `external`, `replacement`, `external-marker`, `writer`.

Thus this LibreOffice 25.2.3.2 / local-XLSX condition exposes an **application-owned native conflict boundary** rather than silently overwriting an externally replaced workbook.

## Audit

Independent audit does not import the GUI controller. It checks frozen runner/scorer hashes, exact retained backend Git blobs, focus identity, mutation ordering, inode/hash transition, modal titles, release state, durable XLSX hash and cells.

`AUDIT.json`: zero errors. Four deliberately corrupted records (wrong cells, missing conflict modal, bad release, bad causal ordering) are all rejected.

## H / T / D / C / U

**H.** LibreOffice may detect an intervening external XLSX replacement between precheck and save and refuse/prompt before stale overwrite.

**T.** One unscored prompt calibration; retained pair-01 harness failure; one frozen complete pair-02 with one stable and one external-replacement arm. No repetitions are used to infer a natural rate.

**D.** RETAIN native conflict/refusal evidence at this exact condition: stable save succeeds, external replacement is preserved and a conflict dialog appears before overwrite. HOLD general GUI or product-runtime promotion.

**C.** Conflict detection may depend on file timestamp/inode/locking policy rather than semantic document identity. `os.replace` changes the inode, so the next one-factor follow-up should mutate the XLSX contents in-place while retaining the same inode.

**U.** One LibreOffice version/filesystem/profile; no collaborative/remote edit, power loss, network share, symbolic-link swap, repeated trial rate, or prompt-action semantics. The experiment does not identify LibreOffice's internal conflict-detection implementation.

## Same-inode follow-up — c254-pair-03

One factor changed: instead of `os.replace`, the external workbook bytes were written through `r+b` into the existing task file followed by truncate/flush/fsync. The runner asserted the inode was unchanged before save.

Frozen order: stable then inplace; one arm each. Runner SHA-256 `b88c328f5567bc7f83e6fb014fe19c1644da798b62eb17f226c8314511ca2cb1`.

| Arm | Durable outcome | Inode mutation | Modal after known format confirmation | Release |
|---|---|---|---|---|
| stable | `office / preview` saved | Calc later saved via its own new inode | none | empty/verified |
| inplace | external workbook preserved | **same inode before/after external rewrite** | `Document Has Been Changed by Others` | empty/verified |

Inplace arm:
- precheck inode `1314421`, SHA-256 `02c9f27e...`;
- after external in-place rewrite: **same inode `1314421`**, SHA-256 `f6df9f69...`;
- after save attempt/conflict prompt: same inode/hash remained;
- independent scorer recovered exactly `external / replacement / external-marker / writer`.

`c254-pair-03/AUDIT.json` reports zero errors and rejects four deliberate corruptions (changed inode evidence, erased conflict prompt, wrong cells, bad release).

### Updated decision

The retained conflict evidence is **not explained by inode replacement alone**. LibreOffice also refused/prompted when the same inode's XLSX content changed between precheck and save. The experiment still does not identify the internal detector: mtime/ctime, file metadata/content checks, locking, or another policy remain plausible.

A next discriminating rung, if needed, should change file content while preserving selected metadata or manipulate timestamp-only signals one at a time. Do not infer semantic document-incarnation tracking from these two pairs alone.
