# T2 source identity, captured before formal allocation

| Artifact | SHA-256 |
|---|---|
| `FREEZE.md` | `e3a7a1838384a2a08a829dc2eeddab7791b1d882914f3adb2a758c5f66ded5e3` |
| `simulate.py` | `925bd0b45f89577f02d7a5ced4d416efec559367e1791a75fd679bcb1ef62981` |
| `audit.py` | `d248c922dd3aee440c4b799093c571d2e3efb15d683417aab558a3e8ea390d0d` |
| `test_construction.py` | `e545f51f23de454d0aa14ceb82229f9dd20ec01e2914fc76b30af07e58bc3db0` |

Construction smoke ran in the pinned container after static compilation and
before this source freeze. Formal image:
`python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
No formal run has occurred at manifest creation.
