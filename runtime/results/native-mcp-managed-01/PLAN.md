# Managed MCP startup live integration
One primary-assistant private WSL Inkscape run seed991117 max2stages.
Same SDK connection calls native_start with timeout0, then bounded waits on
that same launch; no relaunch. View the returned initial image and public goal.
Primary assistant writes exactly one explicit decision for native_submit.
Use finish_after only for a final action. Retrieve scoring/release/cleanup;
poll native_status to verify tracked owner terminal separately. Preserve logs
and all unknown/failure outcomes. No helper model/sensor/Docker restart.
Host tools are not dynamically registered; a persistent SDK bridge remains.
No timing/token/host-utility benefit claim or crash/disconnect cleanup claim.
