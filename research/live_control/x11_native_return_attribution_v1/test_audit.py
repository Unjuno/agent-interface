"""Pre-measurement counterexamples for the independent audit."""
import base64,copy,hashlib,json
import audit
from pathlib import Path

def fixture():
    b=b'\x10\x10\x10\0'*1024;dg=hashlib.sha256(b).hexdigest();rows=[]
    for i in range(32):
        d=10_000_000+i*2_000_000
        rows.append([d,d+50,d+60,d+70,d+170,d+180,d+200,d+210,80,dg,d+300])
    return dict(case=dict(pair=0,arm='process',count=0,order=1),affinity=[0],observer_pid=10,
        origin_ns=1000,end_ns=1000+rows[-1][10]+2000,observer_cpu_ns=100000,rows=rows,pixels={dg:base64.b64encode(b).decode()},
        load=dict(cpu=1,errors=[],cleaned=True,ready=dict(pid=20,tid=20,affinity=[1]),
            before=dict(ticks=3,alive=True,affinity=[1],at_ns=1000),
            after=dict(ticks=10,alive=True,affinity=[1],at_ns=1000+rows[-1][10]+1000),
            final=dict(cpu_ns=10000000,iterations=500,affinity=[1]),exitcode=0,forced=False,stderr=''))
def main():
    cs=dict(observer=0,competitor=1,server=2)
    mutations={
        'row_length':lambda r:r['rows'][0].pop(),
        'early_return':lambda r:r['rows'][0].__setitem__(6,1),
        'due_step_1ns':lambda r:r['rows'][1].__setitem__(0,r['rows'][1][0]+1),
        'float_time':lambda r:r['rows'][0].__setitem__(2,10.0),
        'negative_cpu':lambda r:r['rows'][0].__setitem__(8,-1),
        'observer_affinity':lambda r:r.__setitem__('affinity',[1]),
        'competitor_affinity':lambda r:r['load']['after'].__setitem__('affinity',[0]),
        'dead_child':lambda r:r['load']['after'].__setitem__('alive',False),
        'no_CPU_exposure':lambda r:r['load']['after'].__setitem__('ticks',3),
        'wrong_process':lambda r:r['load']['ready'].__setitem__('pid',10),
        'cleanup':lambda r:r['load'].__setitem__('cleaned',False),
        'pixel_hash':lambda r:r['pixels'].__setitem__(next(iter(r['pixels'])),base64.b64encode(bytes(4096)).decode()),
        'expected_count':lambda r:r['case'].__setitem__('count',512),
    }
    assert audit.check_case(fixture(),cs)
    passed=[]
    for name,fn in mutations.items():
        x=fixture();fn(x)
        try:audit.check_case(x,cs)
        except (ValueError,KeyError):passed.append(name)
        else:raise AssertionError('accepted '+name)
    truth=audit.derive([fixture()]);bad=copy.deepcopy(truth);bad['decision']='FORGED_PASS'
    try:audit.verify_report(bad,truth)
    except ValueError:passed.append('derived_decision')
    else:raise AssertionError('accepted forged decision')
    # Deliberately ordered but changed timestamp: structural audit alone cannot authenticate it.
    a=json.dumps(fixture(),sort_keys=True).encode();x=fixture();x['rows'][0][4]+=1;b=json.dumps(x,sort_keys=True).encode()
    assert hashlib.sha256(a).digest()!=hashlib.sha256(b).digest();passed.append('coherent_1ns_byte_identity')
    result=dict(pass_all=True,valid_control=True,rejected=passed,total=len(passed),
                note='Exact-byte checks are distinct from structural semantic validity.')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
