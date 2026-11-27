import json,sys,traceback
from pathlib import Path
from codex_app_server_client_v2 import CodexAppServerClient
from codex_app_server_command_v1 import direct_command
result={'initialized':False,'scope':'no thread and no model call'}; c=None
try:
 args=direct_command(sys.argv[1])
 c=CodexAppServerClient(args,cwd=sys.argv[2]); c.initialize();result['initialized']=True
except Exception as e:result.update(error=type(e).__name__,detail=str(e)[:500])
finally:
 if c is not None:
  try:c.close(timeout=5);result['close_returned']=True
  except Exception as e:result.update(close_returned=False,close_error=type(e).__name__)
print(json.dumps(result))
raise SystemExit(0 if result['initialized'] and result.get('close_returned') else 1)

