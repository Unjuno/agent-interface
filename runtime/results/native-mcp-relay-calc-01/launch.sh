set -eu
set -C
exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:research/live_control /tmp/agent-interface-mcp-venv/bin/python research/live_control/native_mcp_relay_v1.py -- --allocation-directory results-local/native-mcp-relay-calc-01 --app calc --seed 991122 --max-stages 4 --harness-python /usr/bin/python3 >results-local/relay-calc-responses.jsonl 2>results-local/relay-calc-stderr.log
