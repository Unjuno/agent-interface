# AI-6147-T0-20261002-02 — terminal candidate STOP

**Disposition: `STOP_CANDIDATE_RUNTIME_ERROR / NOT_EVALUATED`.** The single frozen candidate invocation exited 1 after enumerating and writing its 11,020-byte RAW file, then failed while formatting its final stdout summary. The exception was `KeyError: 'enumerated_policy_trees'` at candidate.py line 159; the frozen layer schema uses `policy_tree_count` plus `policy_trees`. The RAW is preserved byte-for-byte but unverified and must not be interpreted as a result.

| Item | Recorded value |
|---|---|
| Allocation | `AI-6147-T0-20261002-02` |
| Main at freeze | `fe0f2117810d52b1997bf1513cf3da68ef6a2278` |
| Candidate source SHA-256 | `2347d25ea8185a9c495c3582852e007d8a6a07afd6a083d04a53ad4a978cd5d7` |
| Auditor source SHA-256 | `944858325f54bf3f45f3298ba0326927dc2ee8ded5b58722ddc0db92a89036e7` |
| Command | `python -I candidate.py --raw RAW.json` |
| Host | Windows PowerShell; CPython 3.11.9; host CPU; standard library only |
| Candidate | 1 invocation; exit 1 |
| Auditor | 0 invocations (candidate was nonzero) |
| Retries / tuning | 0 / 0 |
| RAW | 11,020 bytes; SHA-256 `ef88effdefee71295a818c38830d7113ef6fea58e56e68dd3f593c0ba36890e1` |
| Scope | No model, GPU/CUDA, GUI/game, network, physical input, or container workload |

The result is an implementation STOP, not a method PASS/FAIL and not evidence for or against safe probe identifiability. No fix or retry is permitted for this consumed allocation. The separate raw auditor did not run. All bytes and the failed process outcome are retained for review; a future attempt, if justified, requires a distinct successor allocation and source freeze.

