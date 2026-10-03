# Completed review evidence custody — 2026-10-03

This archive preserves five completed historical review packages associated with merged PRs #6860, #6882, #6885 and #6935. It is an evidence-preservation change, not runtime adoption, a new review vote, or a claim that historical tests pass on today's main.

## Custody and recovery

All 270 tracked source files are retained with exactly their original Git blob IDs and modes. `SOURCE_ENTRIES.tsv` maps each original branch/tip/path to its archive path; `BRANCH_CUSTODY.json` binds complete inventories, source tips, and the related merged PR heads. Five exact source tips are direct parents of the custody commit, after its main first parent. Consequently all original commit histories and original path names remain reachable from main after branch retirement. Restore an original file using its recorded tip and source path, not by guessing an archive-relative name.

Executable source extensions and nested Git control files have a `.txt` suffix in the archive. Thirteen such renames preserve the same bytes and blob IDs; already-inert script copies remain unchanged. Original manifests and source code are deliberately not rewritten: references within them name the historical source layout, not this inert archive. A capsule-level `.gitattributes` disables text conversion. These files are not installed, imported or run by this change. Restoring a runnable historical workspace is a separate, explicitly authorized operation.

| Archive directory | Original tip | Files | Related merged PR |
| --- | --- | ---: | --- |
| `6860_manifest` | `fdaa110b48dc26e7263e9670a1afa3e05d31a1cc` | 72 | #6860 |
| `6882_lineage` | `014b2344a1cc7f43f4aa64dd01518d6b0a72a606` | 42 | #6882 |
| `6885_conjunction` | `24cff4c4eabaee6813f510e0fba22e37ae825d6a` | 32 | #6885 |
| `6935_exit` | `8355e5c2c462317d0845324b90ed8866b54f3690` | 63 | #6935 |
| `6935_late_reply` | `7932dba06c5f691ec93e11c081528e2630daad0c` | 61 | #6935 |

## Qualifications retained, not promoted

- **#6860 manifest:** outside-committee technical evidence, zero counted votes and no apply authority. Historical v1 Python-equality weaknesses, negative source-correspondence checks, setup failures and v2 recursive-JSON repair remain recorded. Reused earlier tests are attributed to their frozen sources. The private combined-source hash is not today's applied main. Finite decoded JSON findings establish neither arbitrary Python/concurrency behavior nor native or physical effects.
- **#6882 lineage:** assigned nonauthor review of one exact combined tree. The first default-path fixture failed with the reviewer's wrong schema literal; its original freeze, source and exit status remain retained alongside the separately frozen repair. A metadata helper's missing `--` separator was a separate setup failure, not a runtime defect. Synthetic inert backend release fields establish no native release. Focused checks are not full current CLI/kernel/CI/platform coverage.
- **#6885 conjunction:** independent reconstruction of 6,144 retained rows and finite typed controls on historical source combinations. It did not rerun author producers or acquire formal resources. Original archive STOP/setup repair and Windows-vs-Git publication ordering failure remain qualified. A reviewer-owned separate runtime component was not self-approved. No arbitrary log authenticity, concurrency, timing, native or performance conclusion is added.
- **#6935 exit:** nominated historical reviewer evidence for the exact v2 tuple, not a new GitHub approval or transferred v1 vote. The first composition failure's missing precise private output is not recovered or invented. Encoding/schema-reader setup failures and their original artifacts remain. Saved current-application tuples, merge receipts, journals and proposed trees are historical records; only GitHub's separately verified merge binds repository application. Caller promise identity and child-absence observations are scoped, not a general release or crash-durability proof.
- **#6935 late reply:** outside-committee evidence with no counted vote/apply authority. Two historical private Windows Node child cases and finite semantic controls remain attributed, including fixture guards, guessed-manifest reader failure, conservative publication STOP and missing-base-blob STOP. Exact first failure UTC/stderr was not captured and is not fabricated. No producer/native/model/container experiment is rerun and no future-main applicability is certified.

Published derivative logs may contain already-redacted private paths or recorded newline normalization. Original/public hash distinctions and lost or private-only receipts remain as supplied by the source packages. This archive preserves available published bytes; it neither reconstructs missing private originals nor rewrites failed results as PASS. Read each retained package README and provenance records for its full scope and limitations.

## Retirement gate

Remote source refs may be deleted only after the custody commit is merged into main, all 270 source-to-archive blob/mode mappings are verified in actual main, all five tip histories are reachable, and a fresh complete open-PR inventory shows no direct head or base dependency. Each deletion is guarded by the exact expected source tip and sent atomically. A changed tip or new dependency aborts the batch. Existing first-parent main entries must remain unchanged. Issue ideas remain unresolved unless separately established; this archive contains no issue-closing directive.
