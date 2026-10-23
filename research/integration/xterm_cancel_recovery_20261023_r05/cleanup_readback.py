"""Read-only post-run process and private-display cleanup snapshot."""
import json,subprocess
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=subprocess.run(['ps','-eo','pid,ppid,pgid,stat,comm,args'],capture_output=True,text=True,check=True).stdout.splitlines()[1:]
xapps=[]
for line in rows:
 fields=line.split(None,5)
 if len(fields)>=5 and fields[4].lower() in ('xvfb','xterm'):
  xapps.append(line)
resources={p:Path(p).exists() for p in ['/tmp/.X191-lock','/tmp/.X11-unix/X191','/tmp/.X192-lock','/tmp/.X11-unix/X192']}
checks={'no_xvfb_or_xterm_processes':not xapps,'private_display_resources_absent':not any(resources.values())}
obj={'schema':'agent-interface/xterm-cancel-recovery-postrun-cleanup-v1','status':'PASS_R05_POSTRUN_CLEANUP' if all(checks.values()) else 'FAIL_R05_POSTRUN_CLEANUP','observed_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'matching_process_rows':xapps,'display_lock_and_socket_exists':resources}
(HERE/'cleanup-readback.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print(json.dumps(obj,indent=2))
if not all(checks.values()): raise SystemExit(1)
