# Construction and execution protocol

1. The exact preregistration and source bytes listed in FREEZE.json are
   mounted read-only. Candidate output and audit output use separate new host
   directories mounted writable.
2. Before each WSLc invocation, verify the source digests and image digest;
   disable network access, use one CPU, 1 GiB memory, uid/gid 65534, and never
   pull an image. Keep every created container and its logs; do not clean it
   up or rerun a failed formal invocation.
3. Run the construction test suite once. Only if it exits zero, run the
   preregistered candidate once. Only if the candidate exits zero, run the
   independent auditor once in a separate container.
4. Preserve stdout, stderr, exit codes, raw output, report, UTC start/end, and
   container inspection details. Record WSLc memory/swap/cgroup warnings
   verbatim. A runtime or audit failure is retained as failure, never repaired
   by mutating frozen sources or retrying.
