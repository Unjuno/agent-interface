import json,os,select,signal,subprocess,tempfile,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
LIVE=ROOT/'research'/'live_control'
DOOM=ROOT/'research'/'doom'
for path in (LIVE,DOOM):
    import sys; sys.path.insert(0,str(path))
OUT=Path(os.environ['V15_OWNER_OUT'])
result={'schema':'v39-v15-process-owner-xvfb-a27-raw-v1','physical_input':False,
        'game_or_model':False,'xvfb_tcp_enabled':False}

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='v15-owner-a27-') as td:
        auth=Path(td)/'Xauthority';auth.write_bytes(b'');env=dict(os.environ,XAUTHORITY=str(auth))
        xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24','-nolisten','tcp','-ac'],
          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        try:
            if not select.select([xvfb.stdout],[],[],5)[0]:raise TimeoutError('Xvfb display deadline')
            number=xvfb.stdout.readline().strip()
            if not number.isdecimal():raise RuntimeError('invalid Xvfb displayfd')
            display=':'+number
            from input_owner_process_v1 import InputOwnerProcess,read_recovery_receipt
            from doom_controller_failure_cleanup_v1 import verify_owner_process_recovery
            owner=InputOwnerProcess(display,OUT/'input-owner-process')
            ready={'event':'input_owner_process_ready','schema':'input-owner-process-ready-v1',
              'owner_id':owner.owner_id,'service_pid':owner.service_pid,
              'service_start_ticks':owner.service_start_ticks,'display':display,
              'receipt_path':str(owner.receipt_path)}
            pid=owner.service_pid;ticks=owner.service_start_ticks;owner_id=owner.owner_id
            owner.close()
            receipt=read_recovery_receipt(owner.receipt_path,expected_display=display)
            verified=verify_owner_process_recovery(OUT,[{'type':'backend_event','event':ready}],timeout=1.0)
            result.update({'display':display,'ready_identity':ready,'receipt':receipt,
              'receipt_sha256':hashlib.sha256(owner.receipt_path.read_bytes()).hexdigest(),
              'normal_gate_verified':verified.get('recovery_verified') is True,
              'service_return_code':owner.process.returncode,
              'receipt_identity_matches':receipt.get('service_pid')==pid and
                receipt.get('service_start_ticks')==ticks and receipt.get('owner_id')==owner_id,
              'owner_thread_stopped':receipt.get('owner_thread_stopped'),
              'empty_verified_close':bool(receipt.get('release_records') and
                receipt['release_records'][-1].get('reason')=='close' and
                receipt['release_records'][-1].get('verified') is True),
              'normal_receipt_gate_accepted':verified.get('service_start_ticks')==ticks})
            result['pass']=bool(result['normal_gate_verified'] and result['service_return_code']==0 and
              result['receipt_identity_matches'] and result['owner_thread_stopped'] is True and
              result['empty_verified_close'] and result['normal_receipt_gate_accepted'])
        finally:
            xvfb.terminate()
            try:result['xvfb_return_code']=xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:xvfb.kill();result['xvfb_return_code']=xvfb.wait(timeout=3)
            result['xvfb_stderr']=xvfb.stderr.read();xvfb.stdout.close();xvfb.stderr.close()
            result['pass']=bool(result.get('pass') and result['xvfb_return_code']==0)
    (OUT/'RAW.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'raw':str(OUT/'RAW.json'),'pass':result.get('pass')}))
    if not result.get('pass'):raise SystemExit(2)

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        result['candidate_error']={'type':type(exc).__name__,'message':str(exc)[:1000]}
        result['pass']=False
        if OUT.exists():(OUT/'RAW.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        raise
