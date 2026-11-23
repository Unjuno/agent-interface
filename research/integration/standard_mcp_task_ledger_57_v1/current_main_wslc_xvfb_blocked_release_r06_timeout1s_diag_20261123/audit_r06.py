#!/usr/bin/env python3
import json
from pathlib import Path
p=Path(__file__).resolve().parent/'runs/optimized-timeout-1s'
r=json.loads((p/'result.json').read_text())
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
need((p/'exit-code.txt').read_text().strip()=='1','R06 expected unittest failure absent')
need(r['status']=='FAIL','R06 structured FAIL absent')
need(r['cancel']['owner_client_disconnect']['status']=='disconnected','R06 disconnect not verified')
need(r['cancel']['owner_release_attempt']['status']=='unknown','R06 release UNKNOWN absent')
need(abs(r['cancel']['owner_release_attempt']['elapsed_ms']-1505.349867)<1,'R06 release timeout value changed')
need(r['independent_release_readback']['neutral'] is False,'R06 held-key readback absent')
need(r['independent_release_readback']['keys_down']['a'] is True,'R06 key A not down at readback')
need(all(v is False for v in r['final_cleanup']['keys_down'].values()),'R06 final fixture cleanup not neutral')
print(json.dumps({'status':'SCOPED_DIAGNOSTIC_CLASSIFIED_NOT_PRODUCT_PASS','disconnect_ms':r['cancel']['owner_client_disconnect']['elapsed_ms'],'release_status':'unknown','release_ms':r['cancel']['owner_release_attempt']['elapsed_ms'],'readback_a_down':True,'final_cleanup_all_up':True},indent=2))