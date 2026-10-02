# Archival qualification — allocation 03

Preserve this consumed allocation as an integrity HOLD. The candidate ran once;
the independent auditor ran once and rejected integrity because the frozen
`unsafe_admission` corruption control changed 1 to 1 and therefore tested no
corruption. Additional archival verification found that the `prepare.py`,
`runner.py`, `audit.py`, `dataset.json`, `PREREGISTRATION.md`, and
`test_contract.py` bytes at the retained branch tip do not match the corresponding
source hashes in `FREEZE.json`. The retained auditor compared candidate-reported
source hash fields to the freeze but did not recompute hashes of these archived
source files. Thus candidate-to-source provenance is not independently
established by this package. Do not rerun either process or alter this
allocation's source, outputs, audit, or verdict. Any follow-up requires a new
allocation and freeze.

| File | Frozen SHA-256 | Archived branch-tip SHA-256 |
| --- | --- | --- |
| `prepare.py` | `caf3cfa72b99a3ab9a4b55dc75792af9923fa10f6b521aae46858c6d0184426b` | `7187f41cd1c1d6aa49d73190b93e006ab472e01308c85f3db6182265ced49ac7` |
| `runner.py` | `7894d649445d40cb19dd42dde9cfc7e252639ac906d605b1a26f7911eb1930ac` | `430cf985f8fc2b3b2c49a57de1b66fab58f1fd7f91aea3d9d850226ae1ec0f17` |
| `audit.py` | `5414860df302e00919ad9c9bf17508b3cf5fadf08f1918d0b9dc93ab32dc86df` | `642d73e2c6ee1328999ccbd69091371fde6fe7476ca74f9206cd6c2d0c2e2ba9` |
| `dataset.json` | `30cf278a2680659744e1407536c1e94b2d7c97785daf5d188e7c0ba2a4f991d6` | `3638186b5d849af7c65bbb1e7255184f5cd99dea803e114047089403cc1336c8` |
| `PREREGISTRATION.md` | `3ee721436f6d4810a6cc56879398bc1ee508572ebd257053a2968087c4a8383e` | `242cde2b2e862a92fb5ef8beddeb2304123d5f505d885903b0f05f5793d03b3d` |
| `test_contract.py` | `9370b089fa57e2e79da02766f098ed496a45301877e5d1c6c8e6a82ee8b9c83f` | `7c2f739bbe39b3af3deea6cbf48dcfb1c85c77856c089ca3171243a5158fc299` |

The candidate bytes are retained as eight base64 shards with the exact byte
length and SHA-256 in `raw_evidence.manifest.json`. `candidate_result.json` is a
pointer, not the reconstructed result. Candidate payload byte integrity is
verified, but its binding to the source files at this branch tip is not. This
archive is not an accepted CPU/CUDA crossover result; timing medians are
descriptive only. It makes no production or broader performance claim.
