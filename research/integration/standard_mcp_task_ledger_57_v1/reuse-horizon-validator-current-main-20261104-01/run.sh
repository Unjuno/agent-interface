set +e
export PYTHONPATH=/workspace/research/integration/standard_mcp_task_ledger_57_v1:/workspace
python3 -m unittest -v test_comparison_measurement_v1 > /evidence/normal.log 2>&1
normal=$?
python3 -O -m unittest -v test_comparison_measurement_v1 > /evidence/optimized.log 2>&1
opt=$?
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$normal" "$opt" > /evidence/exit-status.json
cat /evidence/normal.log
cat /evidence/optimized.log
exit $((normal || opt))