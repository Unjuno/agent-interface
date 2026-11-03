set +e
cd /repo/research/integration/standard_mcp_task_ledger_57_v1
export PYTHONPATH=/repo/research/integration/standard_mcp_task_ledger_57_v1:/repo
python3 -m unittest -v test_comparison_measurement_v1 > /evidence/normal-rerun-01.log 2>&1
n=$?
python3 -O -m unittest -v test_comparison_measurement_v1 > /evidence/optimized-rerun-01.log 2>&1
o=$?
printf '{"normal_exit":%d,"optimized_exit":%d}\n' "$n" "$o" > /evidence/exit-status-rerun-01.json
cat /evidence/normal-rerun-01.log
cat /evidence/optimized-rerun-01.log
exit $((n || o))