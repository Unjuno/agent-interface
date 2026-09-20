# Exact host orchestration invocation

The host orchestration used the corrected harness after the no-model import
failure documented in the pre-registration addendum:

```sh
python3 run_preflight_experiment.py \
  --source-checkout /tmp/issue2849-work \
  --evidence /tmp/issue2849-live-20260921/attempts-live-v2 \
  --codex-exe /opt/homebrew/bin/codex
```

At execution, `/tmp/issue2849-work` was detached at
`6a942ea04bfea1d196d19719ec59a9bdad720826`. The original harness and auditor
are copied beside this file. The attempt/result receipts are authoritative;
the host command's returned cell handle disappeared before its final status
could be collected, so no separate shell exit code is asserted here.
