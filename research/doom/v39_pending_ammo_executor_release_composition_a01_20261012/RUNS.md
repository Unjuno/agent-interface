# Run record

The development preflight passed once in local CPython 3.11 and once in WSLc before the final package freeze. Those runs are not the formal frozen invocation.

The frozen candidate will be invoked once in WSLc 3.0.1.0 using image `sha256:4fc7258eb9f2430d573bcbd352fc9851eee6ce96a65ff026274dfb317119bb7b`, Python 3.14.8, network disabled, `--cpus 1`, `--memory 512m`. One invocation contains the paired soft/hard arms. No retries are planned. An independent auditor runs separately after candidate output is retained.

The WSLc kernel reports swap-limit capability unavailable; memory is requested/limited without swap. No stronger enforcement claim is made.
