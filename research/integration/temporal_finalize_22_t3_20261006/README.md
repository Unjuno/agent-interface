# #22: explicit post-terminal transport finalization

Result: **PASS_TAIL_FINALIZATION_ENGINEERING**. Research helper only; no public-runtime promotion, task-effect or speed claim. This does not close #22/#57/#59 or the repository ROADMAP.

The unchanged T2 `TimedReader.wait()` correctly returns an early historical terminal. Repeating it does not examine remaining transport bytes. The new `FinalizingReader.finalize()` explicitly validates close+EOF, rejects malformed/missing/foreign/trailing records, or returns an unresolved caller timeout. Both preserve the original historical receipt. The baseline is correct for its own historical-only contract, not a false-completion implementation.

One public-hash-frozen allocation (`temporal-finalize-22-t3-20261006-01`) ran 6 tails x2 APIs x2 repetitions:24 fresh receivers, all actual exits0; runner/supervisor exits0; no timeout/forced cleanup/retry/replacement/source tuning. Driver also produces the pipe; no extra producer processes are claimed. Candidate:2 complete,8 error,2 unresolved. Baseline:12 historical-only. Independent raw-only implementation:1080 checks/errors0,12/12 effective evidence mutations rejected. Eight real-pipe units pass normally and with optimization. Same-author separate audit is not external human review.

## Complete evidence, not regenerated fixtures

Seven ordered binary parts contain all38 original UTF-8 study files, including source, H/T/D/C/U plan with variable table/proof, environment, preformal RED/GREEN construction, complete RAW.jsonl, actual execution receipt, frozen audit and controls. Archive24736bytes SHA256 `02dcb9e63010ed3e41e573e0c9bbf499c0112382a0a5458e2690fc89312d174a`. Expanded file map235090bytes. Four exact old dependency sources are included; the earlier T2 full ZIP and old #4220 evidence are NOT asserted republished. Their historical STOP/HOLD remains unchanged.

`finalize_reader.py` is a readable exact copy. Restore first to obtain its dependencies. `restore.py` only decodes checked data; it does not launch any archived program. Use a fresh destination inside a trusted, quiescent parent.

```sh
python -S -B -m unittest -v test_restore
python -S -B restore.py /tmp/temporal-finalize-t3-review
cd /tmp/temporal-finalize-t3-review
python -S -B audit.py evaluation-01 --controls
python -S -B -m unittest -v test_finalize
```

Do not rerun consumed `supervise.py`/`run.py` evaluation. Saved-data audit and regression tests are repeatable checks, not new scientific measurements. Full report is REPORT.md; complete PLAN.md is in the capsule.

## Limits and chronology

Source hash freeze: commit `fc6bd1d73ea42f54c6d01f7b186b40b9ab3984be`, Issue #22 comment6014035650. First outcome comment6014058391. Full source publication follows the result; it was not precommitted in full.

Provided Linux x86_64/CPython3.13.5 isolated execution container, exclusive anonymous pipe,50ms diagnostic deadline. Not WSLc/Docker/OrbStack image attestation or the user's shared host/GPU. No GUI/model/task input/network experiment. Transport closure is neither authenticated source completeness nor current-world evidence, causal completion, action authority or retry permission. Additional finalization incurs work; it is not a speedup. No hard-time bound or natural-fault-rate claim.
