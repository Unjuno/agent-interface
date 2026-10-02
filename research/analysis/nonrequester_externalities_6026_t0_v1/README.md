# Issue #6026 T0 candidate — synthetic accounting only

This is a finite method test, not evidence about people or real notifications. The frozen synthetic fixture offers seven task assignments to two routes, with requester task-effect times and a principal-indexed event ledger covering scheduled approval, redundant pings, a burst, duplicate review, nonresponse, cleanup, and a suppressed notice.

Canonical captured outcome is `results/host-run-06/`; the top-level `result.json` and `audit.json` are byte-for-byte convenience copies of that run's stdout. Earlier incomplete outputs are retained in their own host-run directories with review dispositions.

Run locally:

```sh
python3 -m unittest -v test_method.py
python3 candidate.py fixture.json > result.json
python3 audit.py fixture.json result.json
```

Candidate claim under test: requester-only task-effect time is 28 vs 14 synthetic minutes (`plain` vs `fast`); collaborator active-effort burden is 1 vs 17 minutes by route. Maximum within-burst counts are principal-indexed (three deferrable alerts to collab-b; two redundant pings to collab-a). These are planted fixture values. The method test asks whether the route-indexed ledger makes this requester/bystander trade-off visible; it does not define which party's minutes should dominate or whether any alert caused human interruption. No human attention effect, joint welfare, causal effect, or product benefit is measured.
