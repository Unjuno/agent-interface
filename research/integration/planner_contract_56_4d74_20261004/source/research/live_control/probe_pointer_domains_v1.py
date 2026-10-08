"""Scripted fixed-coordinate integration/stress probe, never assistant speed evidence."""
import argparse,json,hashlib,select,subprocess,sys,time,uuid
from pathlib import Path
from pointer_exchange_v1 import run
from unix_json_deadline import exchange

HERE=Path(__file__).resolve().parent
TASKS={
 'openttd':('openttd_task/results/guard-self-use-01/events.jsonl',['select-and-preview','bounded-road']),
 'mindustry':('benchmark_discovery/results/mindustry-build-self-use-01/events.jsonl',
               ['select-basic-conveyor','restore-plan-and-build','pause-and-review']),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__),*[HERE/n for n in ('pointer_socket_entry_v1.py','pointer_exchange_v1.py','event_socket_v11.py',
             'event_cursor_v5.py','command_once_v2.py','bounded_pipe_writer_v2.py','unix_json_deadline.py','receipt_image.py')]]
    sources += [HERE.parent/relative for relative,_ in TASKS.values()]
    dump(a.out/'plan.json',{'scope':'scripted adapter readiness, fixed known replay; no performance comparison',
        'domains':list(TASKS),'stress':['already expired request: reject before input','cancel active Shift hold: release and cancelled terminal'],
        'mindustry_pre_pause_wait_s':3,'sources':{str(p.relative_to(HERE.parent)):sha(p) for p in sources}})
    for domain,(relative,identifiers) in TASKS.items():
        out=a.out/domain;out.mkdir();runtime=out/'runtime';records=[];exchanges=[];cursor=0;process=None;endpoint=None
        result={'domain':domain,'controller':'scripted fixed-coordinate replay'}
        try:
            args=[sys.executable,'-u',str(HERE/'pointer_socket_entry_v1.py'),domain,'serve','--',
                  '--root',str(a.root),'--out',str(runtime)]
            with (out/'stderr.txt').open('w') as error:
                process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=error,text=True)
            if not select.select([process.stdout],[],[],10)[0]:raise TimeoutError('socket announcement')
            endpoint=json.loads(process.stdout.readline());dump(out/'endpoint.json',endpoint)
            def request(spec,cancel=False):
                nonlocal cursor
                item={'request':spec,'cancel_lane':cancel,'started_ns':time.perf_counter_ns()};exchanges.append(item)
                dump(out/'exchanges.json',exchanges)
                reply=exchange(endpoint['cancel_socket' if cancel else 'socket'],spec,timeout=31)
                item.update(reply=reply,returned_ns=time.perf_counter_ns());dump(out/'exchanges.json',exchanges)
                assert reply['cursor']==cursor+len(reply['records'])
                records.extend(reply['records']);cursor=reply['cursor']
                return reply
            def command(command,events,timeout=5,action_id=None,cancel=False):
                spec={'after':cursor,'events':events,'timeout':timeout,'request_id':uuid.uuid4().hex,'command':command}
                if action_id is not None:spec['action_id']=action_id
                return request(spec,cancel)
            initial=request({'after':0,'events':['observation'],'timeout':30})
            assert initial['status']=='boundary'
            clock=command({'op':'clock'},['clock'])['records'][-1]
            expired=command({'op':'submit','id':'expired','expected_sequence':clock['sequence'],
                             'valid_until_ns':1,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':80}]},['terminal'],action_id='expired')
            assert expired['status']=='unattributed_rejection'
            assert not any(e['event'] in ('accepted','input_admission','pointer_admission') for e in expired['records'])
            hold=command({'op':'submit','id':'cancel-hold','expected_sequence':clock['sequence'],
                          'valid_until_ns':clock['runtime_ns']+10000000000,
                          'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':4000}]},['observation'],action_id='cancel-hold')
            assert hold['status']=='boundary' and any(e['event']=='input_admission' for e in hold['records'])
            cancelled=command({'op':'cancel','id':'cancel-hold'},['terminal'],timeout=1,action_id='cancel-hold',cancel=True)
            terminal=cancelled['records'][-1]
            assert cancelled['status']=='boundary' and terminal['event']=='terminal' and terminal['status']=='cancelled' and terminal['release']['verified'] is True
            result['expired_rejected']=True;result['active_cancel_released']=True
            commands=[r['command'] for l in (HERE.parent/relative).read_text().splitlines()
                      if (r:=json.loads(l))['event']=='command' and r['command'].get('id') in identifiers]
            assert [c['id'] for c in commands]==identifiers
            for index,c in enumerate(commands):
                if domain=='mindustry' and index==2:time.sleep(3)
                call=out/f'call-{index+1}';call.mkdir()
                batch={'records':list(records),'cursor':cursor,'status':'boundary'}
                dump(call/'source-batch.json',batch);dump(call/'steps.json',c['steps'])
                value=run(request,batch,runtime,c['id'],c['steps'],30000,lambda name,v:dump(call/(name+'.json'),v))
                dump(call/'report.json',value)
                assert value['state']=='terminal' and value['terminal']['status']=='completed',value.get('reason')
            final=command({'op':'finish'},['independent_evaluation'],timeout=25)
            evaluation=final['records'][-1]
            result['evaluation']=evaluation
            assert evaluation.get('contract_satisfied',evaluation.get('success')) is True
            process.wait(timeout=10);assert process.returncode==0
            result['success']=True
        except Exception as exc:
            result['success']=False;result['error']=repr(exc)
        finally:
            if process and process.poll() is None:
                # Explicit cleanup only; never replay a task input after uncertainty.
                if endpoint:
                    try:
                        cleanup=exchange(endpoint['socket'],{'after':cursor,'events':['independent_evaluation'],
                            'timeout':25,'request_id':'cleanup-'+uuid.uuid4().hex,'command':{'op':'finish'}},timeout=26)
                        dump(out/'cleanup-reply.json',cleanup)
                    except Exception as exc:result['cleanup_error']=repr(exc)
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
            result['bridge_returncode']=None if process is None else process.poll()
            dump(out/'records.json',records);dump(out/'result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
