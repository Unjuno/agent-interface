# Owner session identity field audit

At frozen PR #7546 head `5f1e8ca5ddfae92c68530fd86668b811e65d2a12`, the
`research/live_control/input_owner_v12.py` source blob is
`f7ec9e6c8e29ce3eb34cc2642cee239f98397d80`. The exact read-only check was:

```text
git grep -n -e session_id -e run_id origin/pr/7546 -- research/live_control/input_owner_v12.py
```

It returned exit 1 with no matching lines. The scorer candidate carries
`run_id`, but the corresponding owner admission/release source has no field to
join against it. T1 therefore requires a shared `session_id` and demonstrates
the contract using synthetic action rows. This is the remaining source-wiring
gap, not a measured live mismatch.
