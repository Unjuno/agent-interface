# Conditions — current-main WSL supported-host diagnostic R03

- Frozen source: `/home/user/agent-interface-preview-main-r05-20261123`, detached at `c5fc0ee00b5fa5208088ee69004a336770336ac4`, full clean checkout.
- Acceptance first outcome: `/home/user/agent-interface-acceptance-r02-20261123`; runner invoked once without `--live` or `--install-dependencies`; no `.venv` existed before or after.
- Doctor invocation: `/home/user/agent-interface-preview-main-r05-20261123/runtime/golden-demo-v3.sh doctor`; system Python selected because `runtime/.venv/bin/python` was absent.
- Separate doctor capture: `/home/user/agent-interface-acceptance-r03-20261123/`.
- Doctor exit: 1; JSON says `passed: false`, 8 of 15 checks passed.
- No dependency/runtime/model/browser/CLI/container download or installation; no GUI, provider, or live-input action.
- The checked-out source and raw first-run outputs are immutable inputs; this packet records diagnostic evidence only.
