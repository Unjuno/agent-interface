from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from durable_token_state_v2 import DurableTokenLedger,DuplicateReceipt,TokenConsumed,TokenMissing,StateError
mode=sys.argv[1]; state=Path(sys.argv[2]); rid=sys.argv[3] if len(sys.argv)>3 else None
try:
    if mode=='issue':
        receipt=json.loads(Path(sys.argv[3]).read_text()); led=DurableTokenLedger(state,initialize=not state.exists()); t=led.issue(receipt); print(json.dumps({'status':'issued','id':t.authority_end_id,'seq':t.post_sequence,'entries':led.entries}));sys.exit(0)
    if mode=='recover':
        led=DurableTokenLedger(state);t=led.recover_pending(rid);print(json.dumps({'status':'pending','id':t.authority_end_id,'seq':t.post_sequence,'entries':led.entries}));sys.exit(0)
    if mode=='revalidate':
        current=int(sys.argv[4]);led=DurableTokenLedger(state);t=led.recover_pending(rid);print(json.dumps({'status':'result','gate':led.revalidate(t,current),'id':rid,'seq':t.post_sequence}));sys.exit(0)
    if mode=='consume':
        led=DurableTokenLedger(state);t=led.recover_pending(rid);led.consume(t);print(json.dumps({'status':'consumed','id':rid,'entries':led.entries}));sys.exit(0)
    if mode=='load':
        led=DurableTokenLedger(state);print(json.dumps({'status':'loaded','entries':led.entries}));sys.exit(0)
except DuplicateReceipt as e:print(json.dumps({'status':'duplicate','error':str(e)}));sys.exit(10)
except TokenConsumed as e:print(json.dumps({'status':'consumed_reject','error':str(e)}));sys.exit(12)
except TokenMissing as e:print(json.dumps({'status':'missing','error':str(e)}));sys.exit(13)
except StateError as e:print(json.dumps({'status':'state_error','error':str(e)}));sys.exit(11)
