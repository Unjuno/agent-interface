# Conditions — current-main WSL Chrome configuration diagnostic R04

- Frozen source: `/home/user/agent-interface-preview-main-r05-20261123`, detached at `c5fc0ee00b5fa5208088ee69004a336770336ac4`.
- Invocation: from that checkout, run `AGENT_INTERFACE_CHROMIUM="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" ./runtime/golden-demo-v3.sh doctor` once.
- Output directory: `/home/user/agent-interface-acceptance-r04-20261123/`.
- The environment override applied only to this doctor process; it did not persist in WSL or Windows environment settings.
- No browser launch or other GUI/input action; no Python package, CLI, browser, runtime, model, or container installation/download.
- Doctor exit code 1, JSON `passed: false`, 9/15 checks passing. Default doctor R03 is retained separately for comparison.
