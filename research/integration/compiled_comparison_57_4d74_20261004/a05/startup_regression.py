import json
from pathlib import Path
from integrated_efficiency_client_capacity_v3 import RuntimeClient,SOCKET_ENTRY
assert not Path('/prior/integrated_efficiency_socket_v1.py').exists()
assert SOCKET_ENTRY==Path('/source/research/live_control/integrated_efficiency_socket_v1.py') and SOCKET_ENTRY.exists()
with RuntimeClient(Path('/out/client'),991075,chromium='/usr/bin/chromium') as client:
 assert len(client.ready['goal']['tasks'])==6
 evaluation=client.finish('startup-only-no-actions')
 assert evaluation['success'] is False and evaluation['record_count']==0 and len(evaluation['missing'])==6
 Path('/out/REGRESSION.json').write_text(json.dumps({'scope':'actual startup and independent no-action evaluation; not formal arm','resolved_socket_entry':str(SOCKET_ENTRY),'evaluation':evaluation,'provider_calls':0,'durable_task_submits':0},indent=2))
print('PASS actual startup; independent six missing, zero submissions')
