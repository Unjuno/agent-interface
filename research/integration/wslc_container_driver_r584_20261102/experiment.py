import hashlib,json,sys,time,uuid
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'source'))
from wslc_driver import ContainerDriver
run=uuid.uuid4().hex;files=['experiment.py','source/wslc_driver.py','source/wslc_cleanup.py','source/recovery.py'];result={'status':'UNKNOWN','run_id':run,'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in files},'started_ns':time.monotonic_ns()}
driver=None
try:
 driver=ContainerDriver(root/'allocation',run,'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25',['python3','-c','import time,sys;time.sleep(3);sys.exit(7)'])
 result['start']=driver.start(timeout_s=15)
 if result['start'].get('status') in ('running','exited'):
  result['wait']=driver.wait(timeout_s=12)
except BaseException as e:result['error_type']=type(e).__name__
finally:
 if driver is not None:
  try:result['reconcile']=driver.reconcile(timeout_s=20)
  except BaseException as e:result['reconcile_error_type']=type(e).__name__
 result['ended_ns']=time.monotonic_ns()
 if result.get('wait',{}).get('status')=='exited' and result['wait'].get('exit_code')==7 and result.get('reconcile',{}).get('remove',{}).get('status')=='observed_absent':result['status']='observed_exit_and_absence'
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'start':result.get('start',{}).get('status'),'wait':result.get('wait',{}).get('exit_code'),'cleanup':result.get('reconcile',{}).get('remove',{}).get('status'),'error':result.get('error_type')}))
