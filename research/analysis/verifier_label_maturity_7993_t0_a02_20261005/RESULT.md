# T0-A02 formal result — Issue #7993

**Disposition: `PASS_METHOD_SCOPED`.** The preregistered native-host allocation executed once, with zero retries. Candidate and auditor each exited 0. The independent auditor reported 64 public cases and 64 complete support states, exact probability mass `1/1`, exact uncapped IPCW expectation `1/2`, and true design risk `1/2`. It found no independent reconstruction errors and rejected all six frozen mutations, including a fabricated finite-cohort claim and estimating through zero support.

The result supports only the exact superpopulation IPCW expectation subgate under the declared finite design and its explicit model assumptions. It does not establish a finite-cohort risk point claim, operational calibration, repeated-cohort performance, live-authority/product effect, or completion of Issue #7993.

Execution was native macOS arm64 / CPython 3.14.5 because OrbStack image inventory failed on a containerd content-blob read (`operation not supported`). No container was used and network isolation was not enforced. The runner records one driver invocation, one candidate invocation, one auditor invocation, and zero retries. The start marker, terminal receipt, frozen manifest, outputs, and logs are preserved alongside this report.

Frozen manifest SHA-256: `04309735e0401e9672e28ac44775dc85893a32aaa1b10704094be3a90834096a`.
