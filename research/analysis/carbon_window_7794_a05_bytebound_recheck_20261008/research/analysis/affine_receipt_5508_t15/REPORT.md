# Issue #5508 T15 — kill after sink INSERT, before COMMIT

## Disposition

**PASS for the preregistered one-case local SQLite crash boundary.** The child reached the barrier emitted after `INSERT` and before `COMMIT`, was killed by SIGKILL (`-9`), and the independent auditor confirmed the committed receipt remained consumed while SQLite recovery exposed no sink row and the target remained unchanged. Recovery is `UNKNOWN`; no replay was attempted.

## Formal evidence

- Preregistration: Issue comment [#5912852871](https://github.com/Unjuno/agent-interface/issues/5508#issuecomment-5912852871), posted before the formal run.
- Base HEAD: `ae727543f47e48bb1686e706b21ed5d9ba1cc31d`.
- Runtime: OrbStack Docker, Linux/ARM64, `--network none`; `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Frozen runner SHA-256: `4163d94e3f600c8238f9e6c8eef71b5f779a29668ad4cad163148caf79d4105a`.
- Frozen auditor SHA-256: `3f11b2414f9479a56d83b18422e9e1cd6e8fdd1fd490e20339ad3ca6748b872f`.
- Frozen mutation-control SHA-256: `a140e392f6d2f5dc9dc8e5b55e43a1b3725862430acde5beba839ec6d7cfd2c9`.
- Raw JSONL SHA-256: `acb797b4959608c7ecd13b19c0cab77c12064b0a0fd55bdf34f8e72a0a1e0976` (`raw/formal/results.jsonl`).
- Independent auditor: `{"audit":"PASS","decision":"PASS","errors":[],"independent_recovery":"UNKNOWN"}`.
- Receipt DB SHA-256: `1386e07eb9ad4a847148a235a53428a70909d6fdbb830bd8e8866138d7e582e3`.
- Recovered sink DB SHA-256: `222cc621cd20950359720a5cb594a32b849eda7fc232b13cf8af2cbde58a8590`.
- Preserved SQLite rollback-journal sidecar SHA-256: `a57ab13ddd571af3bfa298094a7f43d232a7790113aa890c36e701638e70b7da` (`raw/formal/sink.sqlite-journal`). Its bytes are retained without interpreting the journal format; the conclusion is based on reopening the database, observing no delivery row, and the independent audit.

## Mutation-control invocation record

The first post-run control command omitted the pinned image argument. Docker interpreted `python` as the image name, selected an `amd64` default image, then failed to execute the non-executable script path (`permission denied`). The control script did not run. The resulting empty output is preserved as `raw/formal/corruption-controls-attempt-01.empty` (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).

The exact same frozen control script was then invoked once with the preregistered pinned Python 3.12 image. It rejected both forged-success and forged-child-exit mutations (`all_rejected=true`); output SHA-256 `f1d627ce4aeaca59ec9fc9d7b92ff8a15755ff3dda5edee02b3ecd102b6b7d86` (`raw/formal/corruption-controls-corrected.json`). Runner, auditor, formal output, and source bytes were unchanged. This invocation mistake is disclosed; the primary formal experiment and independent audit had already passed.

## Scope

This demonstrates local SQLite rollback recovery for an uncommitted insertion after process death. It is not host power-loss or media-failure evidence, does not atomically couple receipt and sink databases, and says nothing about networked stores, real APIs/GUI, or external semantic truth.
