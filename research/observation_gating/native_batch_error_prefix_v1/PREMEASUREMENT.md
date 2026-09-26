# Issue #4055 premeasurement commitment

Allocation `native-batch-error-prefix-a55f-20260922-01`. This commit is a public hash commitment before the first formal batch. Full source bytes and all raw evidence will be delivered afterward; they are not claimed publicly available before this commit. The earlier receive/hash performance HOLD and all STOPs remain unchanged.

H: an oversized datagram following normal datagrams can make the exact legacy receiver raise after consuming a normal prefix without exposing it. The new result ABI returns prefix and error separately. This is a private cooperative AF_UNIX/SOCK_DGRAM contract experiment, not an OS vulnerability, production change, GUI/model result or performance comparison.

T: eight schedules EMPTY[], CLEAN[A,B], LIMIT[L,A], FIRST[X,A,B], MIDDLE[A,X,B], LAST[A,B,X], DOUBLE[A,X,B,X,C], ZERO[A,Z,B]. A/B/C are distinct 4096-byte synthetic datagrams; L is8192, X8193, Z0 bytes. Three repetitions, two policies,48 fresh sockets/consumer processes. Three immutable16-case batches; policies alternate by repetition+scenario parity. Each consumer executes exactly two reads; parent queues all input first, then independently drains any remainder after the child exits. Parent diagnostics are not candidate delivery. Original receiver.py and receive_batch.c bytes are unchanged, with unused length slots initialized to-1 by the test driver for diagnostic visibility. New native return keeps the same64x8192 capacity,20ms poll and2ms drain but separates fault_errno/rejected_size from prefix count.

D: full48-case/source/byte/order/exit accounting; per policy63 sent,15 oversize errors,3 unread. Legacy30 visible/15 unreported normal prefixes in9 cases; new45 visible/0 unreported. Exact-capacity and zero-length controls retained. Candidate oversized admission, data fabrication or lost prefix is FAIL; missing source/process/schedule evidence is HOLD/STOP. Separate raw-only auditor and14 semantic copied-evidence controls required. No input/replay authority. No retries/replacement/pooling or source/gate tuning after freeze.

C/U: supplied Linux x86_64/CPython3.13.5, installed gcc/glibc; no Docker/OrbStack image attestation, external-network experiment, model/provider, GUI/input or production runtime. Small prequeued sequences; no concurrent sending/close, arbitrary errno, signal, cross-platform, latency or task-effect claim. Same-author separately implemented auditor is not external human approval.

Construction01 has retained child timeout/exit-9 despite printed response; construction02 adds only Python -S to avoid unnecessary site initialization and completes16 cases.18 raw-audit unit methods and14 construction mutations pass. Formal rows are zero at this commitment. This setup incident remains here, not another research Issue.

Exact command directory: `/mnt/data/batch_prefix_study/research/observation_gating/native_batch_error_prefix_v1`.

```
python -S -B invoke.py 0
python -S -B invoke.py 1
python -S -B invoke.py 2
python -S -B audit.py . --out AUDIT.json
python -S -B controls.py . --formal --out CONTROLS.json
```

Each invocation is one external tool call,30s allowance; batch supervisor24s, child1s. A consumed or failed batch cannot be repeated or skipped. Previous actual successful exit and raw digest required. Clock values are diagnostic, not hard-real-time guarantees.

Local FREEZE.json SHA256: `27b099296dd396149eaa32db4da8f0502a7f26e939f0b0c27f00eb3948681085`.

```json
{
  "allocation": "native-batch-error-prefix-a55f-20260922-01",
  "batches": 3,
  "cases_per_batch": 16,
  "created_utc": "2026-09-21T23:01:13.211241+00:00",
  "files": {
    "ENVIRONMENT.json": "f06bc2ee5f470b719ea30b02702af5231f0e36f9fbbfc223ad935d9f9277b61d",
    "PLAN.md": "8cabbb2e36a4b547e70c29adf6f58779159391f735562f6e77c64bce758bcb21",
    "PROVENANCE.json": "c2eb6ec037cb93a3fc05f34f17a1179d684608564dcec8fb9077989fbed41840",
    "SCHEDULE.json": "8165fcaaf30772d092ae196bb207f32db4d3664f934a7bda93399c8f7df27a20",
    "audit.py": "00fcb88808501dbae5feec4ded7baf94fb5195405a1bc6cba89e9557d9bf5f81",
    "build/prefix_receive.so": "1e970a2fce8e8033b566ad1c8de9ecba16ebbc7fb6f9ba28c9ab34fb36e33e47",
    "build/receive_batch.so": "2bf8b7bae60a330b9ba089cd55a4919d1b838cefd547c5340323c816a5044fbb",
    "candidate.py": "752df7efb4f24d98d76ee8b3407821d0e498d936ba49730b8a4f126c068c7957",
    "controls.py": "40fa2eed29b7d57990fab6ad68204e3252370ed3d51a47fc398ba6b243435d77",
    "invoke.py": "1ac1fe08df2a26df782a7663a4cc029b269263c3323b155b3152e94f61b20533",
    "legacy_receive_batch.c": "c30bd022ec551f5d89b41b8657fa066aeb4883d80591527c927ae2e5d32a6439",
    "legacy_receiver.py": "d311c1849d849b2c7c6cd248676045e171d5e0a060c241828e54dc1c5c3fb745",
    "prefix_receive.c": "fbc9c9a2f472134475575e909da4ae3b7dd2eaf9b40627be77c45210a597de71",
    "protocol.py": "ba5945cb380950fce9fa299a0781d6e0b5bb57acde6270dae5d700505cbe19aa",
    "run.py": "3bd3565940c4a0eb516392a97db5a01c82b01ff4776ebdb36f140772a162cf55",
    "test_audit.py": "f5a3906eba275a4147c859f3678cb1d65b52f44002b41cde92d66c64fd8e84f1",
    "worker.py": "49dd47a06ccf5cd173ec5bdc5c66a7b5c7dc298c881e8ee6a160c54311de2ab5"
  },
  "formal_cases": 48,
  "intake_main": "6e5a6dd60cd93aee300cd4bd11712bb9d6bd8520",
  "issue": 4055,
  "old_formal_reexecutions": 0
}
```

Remaining delivery roadmap: remote commitment readback -> three first-outcome batches -> independent raw audit and controls -> full new source/raw/result PR -> exact-head checks/review/main readback. This closes only the scoped new experiment; #2117 and the repository roadmap remain open. The original a55fed37 performance archive remains separately retained rather than falsely claimed uploaded here.
