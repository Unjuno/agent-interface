# G10 pre-dispatch action receipt candidate — 2026-11-15

Base `origin/main`: `f0d5fa202de83f39012bf4a914369b21f8e98a41`; candidate HEAD before this change: `a457d54bb3ea43edd39422ae887099a5002880c5`.

## Change and scope

`runtime/guarded_x11_v1/compiled.py` exposes an optional trusted-caller `before_action_dispatch` hook. After fresh admission, the actual bridge invokes it only when input-guard verification succeeds. The adapter supplies its own action name, minted action ID, operation, last observed process/window generations, same-clock timestamp, and a `bridge._save` evidence reference before guarded input dispatch. The dispatch receipt is persisted before calling profile code; persistence failure therefore prevents input. Public graph input cannot choose this callback. The existing post-release callback remains the source of transition acceptance and release evidence.

The G10 offline composition now joins the pre-dispatch record to the completed transition by exact action ID and checks timestamp ordering. Its save-request contract is v2 and requires the persisted dispatch evidence reference; the later action receipt and save request must carry the same reference. Saved FODS payloads and X11 bridge remain fixtures. This does not implement a public G10 profile and does not establish live Calc, OCR/reference grounding, native GUI effect, or #57 efficiency.

## Verification

Python 3.11.9, Windows host. Commands:

- `python -m unittest runtime.guarded_x11_v1.test_compiled runtime.guarded_x11_v1.test_calc_g10_action_custody_composition runtime.guarded_x11_v1.test_calc_g10_artifact_v1` — 68/68 passed.
- `python -O -m unittest runtime.guarded_x11_v1.test_compiled runtime.guarded_x11_v1.test_calc_g10_action_custody_composition runtime.guarded_x11_v1.test_calc_g10_artifact_v1` — 68/68 passed.
- `python -m unittest runtime.guarded_x11_v1.test_compiled_native_dependencies` — 12/12 passed.
- `python -O -m unittest runtime.guarded_x11_v1.test_compiled_native_dependencies` — 12/12 passed.
- `git diff origin/main..HEAD --check` — passed.

Raw output: `normal.log`, `optimized.log`, `native-guard-normal.log`, and `native-guard-optimized.log` in this directory.

## SHA-256

- `normal.log`: `443fc0bce262198afb1bd2229a1872cc81d94a7b181a8c83ec04c6856167b660`
- `optimized.log`: `83861c3f9d9626de66366deb2a93c9757e7c5cf825fc1dd738cc6fc5c333885a`
- `native-guard-normal.log`: `3a798347f6ea830f103ba542a70a59ee424e5409520f0883333700bffda69cd4`
- `native-guard-optimized.log`: `7db476b39bb645063d7e8f8fdd0cb8ce58283d11a03f5404c3c42401e867c19a`
- `runtime/guarded_x11_v1/compiled.py`: `10ab04d437b99f9685c49f6d3fc2bcd1c1abb412112b18a5dbc73070e4a56ff6`
- `runtime/guarded_x11_v1/test_compiled.py`: `fa20e28a3085c6483268bb9bedd1000482e6c81e4f86e51eb3682ec57389a331`
- `runtime/guarded_x11_v1/calc_g10_artifact_v1.py`: `b6556dbbde886e69ce8e00365976ac1b353035a20947589c96b448ffe6fda893`
- `runtime/guarded_x11_v1/test_calc_g10_artifact_v1.py`: `904b693badb0b5e0f9768179a45900b32bd3cfc02062caca9133eee19b7a1374`
- `runtime/guarded_x11_v1/test_calc_g10_action_custody_composition.py`: `29841a1339b4af53af091c88d7c27716fc6b453ae330988d1622323796e4fa60`

Candidate-only; no push or main modification.

## Final reconciled candidate verification (2026-11-15)

Re-ran the G10/compiled-X11 integration set at candidate HEAD `5fadd3bc86f93b9e8dd6ef4561fa57ade8b27d82`: six modules (`test_compiled`, `test_calc_g10_action_custody_composition`, `test_calc_g10_artifact_v1`, `test_calc_g10_formula_effect_v1`, `test_calc_launcher_v1`, `test_calc_task_artifact_v1`) pass 113/113 normally (4.047 s) and 113/113 under `-O` (3.751 s), Python 3.11.9. The additional three cases relative to the earlier 110 count come from current candidate suite composition. `test_compiled_native_dependencies` passes 12/12 normally (0.218 s) and 12/12 under `-O` (0.226 s).

Raw logs: `final-candidate-g10-six-suites-normal-20261115.log` SHA-256 `577ACDE156C7A71F277C7727B9745C1267E4AB8D54512947DB1CB88734153830`; `final-candidate-g10-six-suites-optimized-20261115.log` `61364638034F86D51D44E92F2B9FDB8C65C976362177BA0C178C07C7A8876603`; `final-candidate-x11-native-deps-normal-20261115.log` `D156564F287232BE78A289122C75B303EEF48A39CE9FFC3E692477E2245D1044`; `final-candidate-x11-native-deps-optimized-20261115.log` `42E6223ED005C5945BAD15AB09C304114351175C479E7EE0037DB57133173814`. Source hashes at tested HEAD: `runtime/guarded_x11_v1/compiled.py` `10AB04D437B99F9685C49F6D3FC2BCD1C1ABB412112B18A5DBC73070E4A56FF6`; `runtime/guarded_x11_v1/calc_g10_artifact_v1.py` `B6556DBBDE886E69CE8E00365976AC1B353035A20947589C96B448FFE6FDA893`.

Scope remains offline fixture/caller and native dependency contract. These checks do not establish live Calc, X11 GUI effects, or #57 integrated economics.
