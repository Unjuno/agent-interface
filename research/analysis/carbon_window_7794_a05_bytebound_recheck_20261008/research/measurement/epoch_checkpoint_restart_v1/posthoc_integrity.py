import argparse,json

def verify(result_path,schedule_path):
    r=json.load(open(result_path)); s=json.load(open(schedule_path)); e=[]
    if r.get('seed')!=s.get('seed'):e.append('seed')
    if r.get('cases')!=s.get('cases'):e.append('cases')
    if r.get('formal_invocations')!=1:e.append('formal_invocations')
    if r.get('reruns')!=0:e.append('reruns')
    if r.get('decision')!='PASS_EPOCH_CHECKPOINT_RESTART_SCOPED':e.append('decision')
    return e

def main():
    p=argparse.ArgumentParser();p.add_argument('--result',required=True);p.add_argument('--schedule',required=True);a=p.parse_args();e=verify(a.result,a.schedule)
    print(json.dumps({'posthoc':'PASS' if not e else 'FAIL','errors':e},sort_keys=True));raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()
