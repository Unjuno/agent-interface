# SHA-256 manifest

Hashes cover the retained report, source runner, construction/candidate JSON, and the exact per-arm summary files written by `_run_arm`.

| File | SHA-256 |
|---|---|
| `REPORT.md` | `6DAA7733F3BAC947EE98D2A6EE9536FE29CF2348A9CEDA06D640752F4738681C` |
| `run_experiment.py` | `C40B64AEA0F0A970FD8AAED3238E3EC05B2F3067B214F164D83E14CEE081E228` |
| `construction_result.json` | `0BC401E8E87898FA89461CB60AD3677E67F61EB97396A33011D1027AE120A1C1` |
| `raw_trace.json` | `58C5D112EECA112B43BD458AD2A6D06DCF260E41F9E825DA9B55408F5E56DD0A` |
| `candidate/A/pair-00/bounded_recovery/arm-summary.json` | `603204B3655EDFF17FD2D33748EC5226AC4DCB7FD9D529DB03B1794C8BE67405` |
| `candidate/B/pair-00/bounded_recovery/arm-summary.json` | `4F18B83F8C226431D6A9F6F6E93BCC325AE7AE53E9111769FFEDE6729894407A` |
| `construction/pair-00/bounded_recovery/arm-summary.json` | `33D67D1D9B94BCDD9D38EA9213C4C935BBCA530EE61AECAECE9E000FC322F9BD` |

The manifest intentionally does not hash itself.
