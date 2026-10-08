set -eu
set -C
exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:research/live_control /tmp/agent-interface-mcp-venv/bin/python research/live_control/native_mcp_relay_v1.py -- --allocation-directory results-local/native-combined-roundtrip-01 --app inkscape --seed 991123 --max-stages 2 --harness-python /usr/bin/python3 >results-local/native-combined-roundtrip-01-responses.jsonl 2>results-local/native-combined-roundtrip-01-stderr.log
