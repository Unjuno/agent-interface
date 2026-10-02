import asyncio,json,sys,time
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from runtime.cli_v1.test_post_dispatch_capture import PostDispatchCaptureTests
from runtime.cli_v1.public_summary import summarize_public_dispatch
real=time.monotonic_ns;start=real();rows=[]
def diagnose(view,**kwargs):
 raw=view['receipt']['source']['raw_report'];ex=raw['result']['execution'];rows.append({'started_ns':ex['started_ns'],'ended_ns':ex['ended_ns'],'waits':ex['waits'],'execution_time_order_valid':ex['ended_ns']>=ex['started_ns']});return summarize_public_dispatch(view,**kwargs)
async def run():
 with patch('time.monotonic_ns',side_effect=lambda:20_000_000_000+real()-start),patch('runtime.cli_v1.public_summary.summarize_public_dispatch',side_effect=diagnose):
  try:await PostDispatchCaptureTests().exercise(include_prior=False,wait_ms=20,expect_summary=True)
  except AssertionError as e:result={'status':'REPRODUCED_FAILURE','error':str(e),'rows':rows}
  else:result={'status':'NO_FAILURE','rows':rows}
 print(json.dumps(result));Path(__file__).with_name('reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
asyncio.run(run())
