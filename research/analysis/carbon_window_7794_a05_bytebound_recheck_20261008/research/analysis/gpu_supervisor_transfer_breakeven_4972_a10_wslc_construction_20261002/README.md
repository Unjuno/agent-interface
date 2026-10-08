# WSLc CPU construction verification — allocation-10 package (2026-10-02)

## H / T / D / C / U

**H.** The frozen allocation-10 preparation tests and auditor mutation controls run under the already-cached PyTorch image in a WSLc CPU-only container with network disabled and the package mounted read-only.

**T.** One WSLc invocation, WSLc 3.0.1.0, linux/amd64 image `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067` (image ID `sha256:048a0de5d4322054f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32`). `--pull=never --network none --cpus 1 --memory 1g`; read-only bind mount of the frozen package; `PYTHONDONTWRITEBYTECODE=1`; no GPU flag and no output mount. Before launch, all 12 files listed in the package `SHA256SUMS` matched their local SHA-256 values.

**D.** Container exited 0. Contract suite 3/3 passed; unsafe-admission construction controls 3/3 passed; full-auditor construction baseline passed, and all 6/6 result mutations plus 2/2 source-byte mutations were rejected. Raw combined output is retained in `CONSTRUCTION.stdout.log` (SHA-256 `b8233922a0a39182940e864310eb9fd62bd6f3fdbf3b90ba570cb71fbb916d74`).

**C.** This is CPU construction/portability evidence for the package only. WSLc emitted its kernel swap-limit/cgroup warning. Although CPU and memory limits were configured, this run did not capture cgroup readback; enforcement is not claimed.

**U.** This does not run the formal timing candidate, CUDA, an actual raw-result audit, or a model/GUI workload. Formal candidate=0, CUDA=0, formal auditor=0, retries=0. No scientific break-even result follows.

The ephemeral WSLc container used `--rm`; a post-run inventory showed no remaining WSLc containers. The frozen package and its formal allocation conditions remain unchanged.
