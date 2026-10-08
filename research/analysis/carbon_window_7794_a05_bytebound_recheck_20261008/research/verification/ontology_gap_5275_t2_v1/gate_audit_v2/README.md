# T2 gate-integrity maintenance successor

## Result

`PASS_GATE_INTEGRITY_CORRECTION_SCOPED` on one frozen retained-input invocation.
The original scientific result remains `FAIL_HELDOUT_LEXICAL_BOUNDARY`, with
8/8 supported false abstentions and 2/8 OOD false passes under the combined
policy. Its original files and negative result are unchanged.

The original T2 auditor checks two gate values, so this is narrower than T1's
empty-map problem: empty T2 gates are already rejected. It fails to validate
the count gate and complete typed gate map. In the retained comparison, it
accepted all five altered copies (false count gate, missing count gate, extra
gate, integer one for a true gate, integer zero for a false gate). The successor
rejects all five with `gates` and returns `NOT_VALIDATED` for their scientific
disposition. Canonical JSON comparison correctly marks every negative copy as
different from the original, including integer/Boolean representations.

The successor independently reconstructs all 16 row decisions, complete arm
metrics, family counts, the exact three T2 gates, and the scientific verdict.
It imports neither candidate.py nor run_t2.py. The actual CLI pins reference
source bytes. All eight test methods passed, including finite/type checks,
count/family/row corruption, original integrity-valid FAIL, and false-PASS
relabel rejection. An explicit synthetic coherent PASS fixture confirms the
checker is not hardcoded to the observed FAIL; that fixture is test data,
not another observed scientific result.

## Evidence and identity

- Original PR: https://github.com/Unjuno/agent-interface/pull/5462
- Source head: `6e320bf71ef4f7139a57d5cc60e7fa84a69b1597`
- Original raw SHA-256:
  `a1db4a23028d91ce2dba0f92c62c24833678845df4721794cb7e8f1334087321`
- Additive freeze SHA-256:
  `a04500ebf974aa3adc02718a98bff2156fd384e97d7ff37dd76c2725eaae3731`
- First receipt SHA-256:
  `bd31177ccfcd6ffae100aac3d9102b14d49c1d7b7d8a89cb66b2fd1a30e5e4a7`
- `SOURCE_ACQUISITION.json` records the seven original Git blobs and hashes
- `retained-01/` includes all copied raw controls and old/new audit results,
  eight-method test transcript, separate CLI output and full execution receipt
- `launch-01/` retains exact command, stdout, stderr and exit 0
- All eleven frozen input/source hashes were checked before any audit call
  and remained unchanged after verification
- Independent source/protocol review preceded invocation; independent
  read/parse/hash result review approved the retained output without rerunning
- No scientific candidate, training, runner, model, network, GPU, GUI or effect
  execution occurred

The existing Linux x86_64 workspace used CPython 3.12.14. Affinity was narrowed
to one CPU, RLIMIT_AS to 256 MiB per process, CPU time to 15 seconds per process,
and the outer wall timeout to 30 seconds. Wrapper elapsed was 62.277 ms;
parent and child peak RSS were each 15,964 KiB. These are single-run diagnostic
observations, not performance comparisons or an aggregate cgroup reservation.
No nested Docker/OrbStack execution is claimed.

Construction logs retain the placeholder TDD RED phase (17 failures) and
eight-method GREEN result. Development placeholder failures are distinct from
the actual original-auditor counterexamples in `retained-01/CONTROLS.json`.

## Read-only recheck

From the repository root:

```sh
python3 -B research/verification/ontology_gap_5275_t2_v1/gate_audit_v2/audit_v2.py \
  research/verification/ontology_gap_5275_t2_v1/FORMAL-01.json
python3 -B -m unittest discover \
  -s research/verification/ontology_gap_5275_t2_v1/gate_audit_v2 -p 'test_*.py'
```

The single retained wrapper invocation has been consumed and is not retried.
Subsequent reviewers may run the read-only verifier/tests as maintenance checks
with their own receipts. They do not need to rerun science.

## Limits

This is metadata/typed numerical audit coverage, not evidence that the original
negative result was incorrect. The retained surface-disjoint corpus is still
synthetic and hand-authored, with no population-representative semantic claim.
No runtime, task quality, safety or product conclusion follows. Declared
side-effect zeros are consistency checks rather than new historical execution
observations. Duplicate JSON keys and hostile reference corpora remain outside
scope. The complete repository is absent from this sparse MCP acquisition;
full-repository CI/build/tests were not run. Publication and merge are separate.
