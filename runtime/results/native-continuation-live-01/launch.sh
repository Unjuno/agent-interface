set -eu
set -C
exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:research/live_control /tmp/agent-interface-mcp-venv/bin/python results-local/pacing-relay.py -- --allocation-directory results-local/native-mcp-continuation-live-01 --app inkscape --seed 991123 --max-stages 2 --harness-python /usr/bin/python3 >results-local/continuation-live-responses.jsonl 2>results-local/continuation-live-stderr.log
