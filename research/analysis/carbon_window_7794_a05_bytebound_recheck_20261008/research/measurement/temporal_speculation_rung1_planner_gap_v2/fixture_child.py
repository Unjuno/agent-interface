import json,sys,time
REALIZE_DELAY_NS=10_000_000
state=int(sys.argv[1])
t0=time.perf_counter_ns(); target=t0+REALIZE_DELAY_NS
while time.perf_counter_ns()<target: time.sleep(0.0002)
t_realized=time.perf_counter_ns()
print(json.dumps({'event':'REALIZED','state':state,'t_realized_ns':t_realized}),flush=True)
line=sys.stdin.readline()
t_recv=time.perf_counter_ns()
try: cmd=json.loads(line)
except Exception:
    print(json.dumps({'event':'TERMINAL','effect':False,'wrong':True,'t_recv_ns':t_recv}),flush=True);raise SystemExit(2)
valid=(cmd.get('expected_state')==state and cmd.get('authority') is True and cmd.get('fresh') is True)
if valid:
    time.sleep(0.0005); t_effect=time.perf_counter_ns()
    print(json.dumps({'event':'EFFECT_APPLIED','effect':True,'wrong':False,'t_recv_ns':t_recv,'t_effect_ns':t_effect}),flush=True)
else:
    print(json.dumps({'event':'TERMINAL','effect':False,'wrong':True,'t_recv_ns':t_recv}),flush=True)
