# Current-main public G10 stdio recheck — R01/R02

Tested code revision: `5dab476e1cdc7248e452e927e3a358f95e548f67`. The code paths and fixture blobs pin identically on current main `704ea90c3c3a4ed58a0d10e67674411b16ec7659`, which adds the crosswalk documentation update. Python 3.11.9 on Windows.

## R01 sparse-input failure

Normal and optimized runs used the exact same test module before sparse checkout materialized its two archived FODS inputs. Both logs contain a `FileNotFoundError` for the pinned `first.fods` path, and the unittest fails while asserting the G10 profile response. The two logs are retained. R01's shell exit codes were not separately captured. This is an environment-custody failure and is not counted as a product test pass or regression.

## R02 materialized-input recheck

Only the main-pinned `first.fods` and `second.fods` fixtures were materialized. The same public MCP stdio module then passed 3/3 in normal mode and 3/3 under `-O`, both with exit code 0. Each R02 log contains the complete public attempt ledger. It records profile `calc-g10-two-save-v1`, two fixture saved-byte effects verified, `input_release_verified=true`, `owner_close_status=closed`, and `replay_allowed=false`. Provider usage remains `unknown_unobserved_by_fixture` with no usage value. The suite covers the public G10 receipt/parent-effect transport and two failure-ledger controls. The test server uses process-owned Fake X and archived FODS; it does not launch Calc. Its `task_success=true` is the result of scoring those archived fixture bytes, not a newly caused live application task.

The recheck confirms current-main public profile and custody behavior for this synthetic stdio fixture. It does not establish live Calc saves, OCR acquisition, real provider usage, MAP01, a matched efficiency result, or recovery reliability. The integrated profile gate is present; a prospectively frozen live same-model lifecycle comparison remains open.
