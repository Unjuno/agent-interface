# MAP01 retained key-up observability boundary

Small offline construction associated with #59 and #5156. It analyzes only
already-retained v38/v39 event streams; it neither accesses Docker/Xvfb nor
replays any candidate, game or input. Start with `PLAN.md`, then `RESULT.md`.

```sh
python3 -m unittest -v test_analyze.py  # construction suite, before freeze
python3 analyze.py                     # frozen analyzer; executed once
sha256sum -c SHA256SUMS
```

Source/report scope and limitations are explicit in `FREEZE.json` and
`RESULT.json`. This result cannot substitute for #5156's live owner-thread
key-up timestamp allocation.
