set -eu
set -C
exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:research/live_control /tmp/agent-interface-mcp-venv/bin/python results-local/pacing-relay.py -- --allocation-directory results-local/native-mcp-relay-calc-paced-01 --app calc --seed 991122 --max-stages 4 --text-gap-ms 2 --harness-python /usr/bin/python3 >results-local/relay-calc-paced-responses.jsonl 2>results-local/relay-calc-paced-stderr.log
