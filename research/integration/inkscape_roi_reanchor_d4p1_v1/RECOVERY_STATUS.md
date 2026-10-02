# Recovery status — #4359 d4p1

This is post-freeze delivery metadata. It is outside the original `FREEZE.json` file set and does not alter the experiment source, schedule, thresholds, or reported first outcome.

## Preserved frozen source

- Original branch head: `73f4d5364265d61d725ee96e59c049e94343015b`.
- The seven public source-capsule parts and `FREEZE.json` are preserved byte-for-byte.
- Data-only recovery verified the decoded XZ/TAR SHA-256 `9933990c85fe8a7f2bccb14012d81bd19655e0eed45e93e1255e51deea67acc4`, 18 members / 64,387 expanded bytes, every frozen member hash, and the published `FREEZE.json` SHA-256 `399267bed798f23b1fc8309bb39b06d71cc289a1eabb276dc3d43a18177d178a`.
- The capsule's freeze records `formal_invocations: 0`; this is the preformal source commitment. Issue #4359 later reports a completed 30-case formal allocation. This source-only archival PR does not contradict, reproduce, or independently verify that later reported result.

## Formal result delivery remains HOLD

Issue #4359 reports `PASS_REANCHOR_RECOVERY_SCOPED`, with 30 formal cases, raw audit and controls. The exact formal raw/result/audit/control package is not present in the original branch tree or this PR. The 16 Actions runs associated with the branch expose no downloadable artifacts. Therefore the Issue-reported PASS remains historical until the exact result bytes are recovered, published, and independently re-audited; no raw rows are reconstructed from summary comments.

## Local checks and limits

On 2026-10-02, the recovered 18-member source capsule passed every declared archive/member hash check. All eight Python modules passed syntax compilation. The frozen unit suite could not run on this host because it lacks Pillow (`ModuleNotFoundError: PIL`); the frozen environment specifies Linux/CPython 3.13.5/Pillow 12.3.0. No package was installed, no shared container was started, and no GUI/formal case was rerun. These local checks do not establish the formal result.

Keep Issue #4359 open and retain the original branch as the recovery pointer for its missing formal package. Merging this recovery PR means only that the frozen source capsule and the result-publication HOLD are discoverable on main; it does not complete the research allocation or its raw-evidence delivery gate.
