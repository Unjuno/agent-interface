# Claim preservation when experiment runtimes disappear

Updated 2026-10-16 from [Issue #8905](https://github.com/Unjuno/agent-interface/issues/8905).

- **Status:** Open, unverified transfer/method idea. No repository defect,
  evidence loss, or risk to current experiments is claimed.
- **Idea:** Distinguish five preservation levels for an analysis-only evidence
  package: byte **FIXITY**, **INTERPRETABLE** schemas and scope,
  independently **AUDITABLE** claims from retained raw data,
  **RE-EXECUTABLE** candidate code in its pinned/reconstructed environment,
  and independently **REPRODUCED** output. A successful raw-only audit is not
  the original experiment and does not establish re-execution or reproduction.
- **Why separate it:** Existing hashes, source/runtime identities and retained
  auditors establish provenance and declared byte integrity. They do not show
  whether a later reviewer can still interpret or check the claim after an
  image, package index, or runner becomes unavailable. A GUI/model outcome may
  depend on nondeterministic external state that an archive cannot recreate.
- **Proposed minimum test:** Freeze three non-sensitive, analysis-only packages
  spanning a standard-library audit, pinned Python dependencies, and a
  container-bound candidate. Verify manifests, then use byte-verified copies
  in an offline arm where the original runtime/image is unavailable and a
  documented fallback arm where eligible. Independently classify each level,
  record the first failure, and check whether a narrower claim remains
  auditable. No historical artifacts are modified; no network, image pull or
  build, model, GUI, or live allocation is used.
- **Observed host audit follow-up (2026-10-16):** On the current-main source
  snapshot `1ece47014d05db898bf73afcd722a14524462e15`, the three existing
  raw-only auditors were each invoked once against their retained evidence;
  no candidate was invoked. #5749 returned `PASS_METHOD_SCOPED` for 78 rows
  and rejected all seven mutation probes. #6530 returned `PASS` for 8 rows.
  #6590 returned `HOLD_AUDIT_INTEGRITY` after reconstructing 10 models and
  30,720 prediction rows, with hash, independent-refit, and prediction
  reconstruction mismatches. That audit ran under Python 3.14.5 / NumPy 2.5.2,
  while the package pins NumPy 1.26.4; this host result does not isolate the
  cause of the mismatches. It does not establish the proposed offline arm:
  inputs were not copied, network isolation was not applied, and no preservation
  levels or fallback arm were evaluated. The three-package test therefore
  remains unverified. Detailed audit output stayed outside the repository.
- **Decision boundary:** A method-scoped pass requires repeatable independent
  level assignment and at least one package that remains auditable after
  re-execution becomes unavailable. Ambiguous classifications or a silent
  change in claim scope fail the method; unsuitable package selection is
  inconclusive. Three packages cannot establish long-term preservation.
- **Related work:** #60 (provenance reconstruction), #1945 (evidence hashes
  and audits), #5082 (atomic publication), #3352 (real-experiment merge gate),
  and #8885 (benchmark-wave comparability). The proposal concerns usability of
  claims under loss of their execution substrate, not replacement of those
  controls.

The issue cites [ReproZip](https://www.usenix.org/system/files/conference/tapp13/tapp13-final16.pdf),
[ACM artifact review and badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current),
and [NIST SP 1500-18r2](https://doi.org/10.6028/NIST.SP.1500-18r2) as related
provenance and preservation guidance. These sources do not validate the
proposed repository-specific levels or test.
