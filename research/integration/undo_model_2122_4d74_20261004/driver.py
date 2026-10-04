import pathlib,json,subprocess,time,hashlib,datetime
R=pathlib.Path(__file__).resolve().parent;O=R/'output';P=json.loads((R/'PLAN.json').read_text());I=json.loads((R/'INPUTS.json').read_text());F=json.loads((R/'FREEZE.json').read_text());rows=[];stop=None
for n,d in F['files'].items():
    if hashlib.sha256((R/n).read_bytes()).hexdigest()!=d:raise RuntimeError('freeze:'+n)
for spec in I:
    name=spec['case'];answer=O/(name+'.answer.json');args=[P['CLI'],'exec','--ephemeral','--ignore-user-config','--skip-git-repo-check','--sandbox','read-only','--json','--color','never','--model',P['model'],'-c','model_reasoning_effort="low"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','--cd',str(R/'empty-workspace'),'--output-schema',str(R/'SCHEMA.json'),'--output-last-message',str(answer),'-'];(O/(name+'.argv.json')).write_text(json.dumps(args,indent=2));start=time.monotonic_ns();started=datetime.datetime.now(datetime.timezone.utc).isoformat();timed=False
    try:r=subprocess.run(args,input=(R/spec['prompt']).read_bytes(),capture_output=True,timeout=P['seconds_per_call']);stdout=r.stdout;stderr=r.stderr;code=r.returncode
    except subprocess.TimeoutExpired as e:stdout=e.stdout or b'';stderr=e.stderr or b'';code=None;timed=True
    ended=datetime.datetime.now(datetime.timezone.utc).isoformat();elapsed=time.monotonic_ns()-start;(O/(name+'.stdout.jsonl')).write_bytes(stdout);(O/(name+'.stderr.log')).write_bytes(stderr);events=[];parse=[]
    for line in stdout.splitlines():
        try:events.append(json.loads(line))
        except Exception:parse.append(line.decode(errors='replace'))
    tools=[e for e in events if e.get('item',{}).get('type') not in (None,'agent_message','reasoning')];usage=[e.get('usage') for e in events if e.get('type')=='turn.completed'];decision=None;error=None
    if answer.exists():
        try:decision=json.loads(answer.read_text())
        except Exception as e:error=str(e)
    ok=code==0 and not timed and not parse and not tools and isinstance(decision,dict) and set(decision)=={'action','reason'} and decision['action']==spec['expected']
    row={'case':name,'started_utc':started,'ended_utc':ended,'elapsed_ns':elapsed,'exit_code':code,'timeout':timed,'usage_reports':usage,'events':events,'unparsed_lines':parse,'tool_items':tools,'answer':decision,'answer_parse_error':error,'expected':spec['expected'],'gate':'PASS_KNOWN_RECEIPT_INTERPRETATION' if ok else 'STOP_FIRST_OUTCOME'};rows.append(row)
    (O/'RESULT.json').write_text(json.dumps({'rows':rows,'attempted_calls':len(rows),'censored_cases':len(I)-len(rows),'stop':None if ok else name,'disposition':'MODEL_INTERPRETATION_PASS_SCOPED' if len(rows)==len(I) and ok else 'HOLD_INCOMPLETE_OR_FAILED','limits':P['U']},indent=2)+'\n')
    print(json.dumps({'case':name,'exit':code,'timeout':timed,'gate':row['gate'],'action':None if decision is None else decision.get('action'),'usage_reports':usage}),flush=True)
    if not ok:stop=name;break
raise SystemExit(0)
