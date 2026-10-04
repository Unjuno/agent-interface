# MAP01 v15 final-scorer cleanup regression

This package reproduces and repairs a cleanup defect at PR #7474 head
`3e498aebd77e500d5a7b1ac9d434d37350a9f597`. `_GameProxy.close()` sampled the
final scorer before closing the wrapped game. A scorer exception therefore
prevented `DoomGame.close()` from running and left the proxy marked open.

The regression test uses a fake game and a raising scorer; it does not import
or launch ViZDoom, X11, models, or physical input. It asserts that game close is
attempted once, the proxy is marked closed, the scorer error remains primary,
and a simultaneous game-close error is preserved as its cause.

The frozen baseline is the byte-exact PR source. The red run uses that baseline
through `SESSION_MAP01_V15_SOURCE`; the green run imports the candidate source.
Both outputs and exit codes are retained here. Relevant neighboring cleanup,
session-selection, and executor tests also pass (9 + 1 + 1 + 2 tests). The wider
`research/doom` session-version discovery run had 6 unrelated host/environment
errors: missing `vizdoom` imports in older versions, Windows pipe/select
`WinError 10038` in v10/v11, and v13 composition. Those results are not used as
evidence for live behavior.

## Reproduction

From repository root:

```powershell
$env:SESSION_MAP01_V15_SOURCE = 'research/doom/results/map01-v39-session-close-failure-pr7474-c09-20261004/BASELINE-session_map01_v15.py'
python -B research/doom/results/map01-v39-session-close-failure-pr7474-c09-20261004/test_session_close_cleanup.py -v
Remove-Item Env:SESSION_MAP01_V15_SOURCE
python -B research/doom/results/map01-v39-session-close-failure-pr7474-c09-20261004/test_session_close_cleanup.py -v
```

`raw.json` records source hashes, outcomes, exact related test commands, and
the scope boundary. `audit.py` verifies the pinned PR baseline, source identity,
the red/green exit codes, and the package checksum list.
