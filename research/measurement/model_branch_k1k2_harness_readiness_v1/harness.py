import json
FORBIDDEN={'authority','grants_input_authority','os_action','coordinate','coordinates','x','y','click','keypress'}
ALLOWED_ACTIONS={'CONTINUE_LEFT','CONTINUE_RIGHT','YIELD'}
TEMPLATE='''You are producing dormant no-authority speculative futures for a fixed synthetic context.\nCONTEXT={"intent":"maintain_tracking","current":"CENTER","history":"LEFT_TO_CENTER","candidate_universe":["LEFT","RIGHT"],"input_authority":false}\nMAX_BRANCHES=@\nReturn exactly one JSON object with key "branches". Each branch must contain exactly branch_id,predicate,semantic_action,no_authority. Produce exactly MAX_BRANCHES branches. branch_id must be unique. predicate must be a symbolic future-state label. semantic_action must be one of CONTINUE_LEFT,CONTINUE_RIGHT,YIELD. no_authority must be true. Do not output OS actions, coordinates, permissions, explanations, or additional keys.\n'''

def prompt(n):
    if n not in (1,2): raise ValueError('K must be 1 or 2')
    return TEMPLATE.replace('@',str(n),1)

def prompt_diff():
    a=prompt(1).encode();b=prompt(2).encode()
    diffs=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    return {'same_length':len(a)==len(b),'diff_count':len(diffs),'diffs':diffs,'bytes':[(a[i],b[i]) for i in diffs]}

def parse_answer(text,k):
    x=json.loads(text)
    if not isinstance(x,dict) or set(x)!={'branches'} or not isinstance(x['branches'],list) or len(x['branches'])!=k: raise ValueError('exact branch count/object required')
    ids=set()
    for b in x['branches']:
        if not isinstance(b,dict) or set(b)!={'branch_id','predicate','semantic_action','no_authority'}: raise ValueError('branch fields')
        if any(key in FORBIDDEN for key in b): raise ValueError('authority/action leak')
        if not isinstance(b['branch_id'],str) or not b['branch_id'] or b['branch_id'] in ids: raise ValueError('branch id')
        ids.add(b['branch_id'])
        if not isinstance(b['predicate'],str) or not b['predicate']: raise ValueError('predicate')
        if b['semantic_action'] not in ALLOWED_ACTIONS: raise ValueError('semantic action')
        if b['no_authority'] is not True: raise ValueError('no_authority')
    return x

def extract_jsonl(lines,started_ns,arrivals):
    events=[json.loads(x) for x in lines if x.strip()]
    msgs=[(i,e) for i,e in enumerate(events) if e.get('type') in ('item.completed','agent_message.completed') and (e.get('item',{}).get('type')=='agent_message' or e.get('type')=='agent_message.completed')]
    turns=[e for e in events if e.get('type')=='turn.completed']
    if len(msgs)!=1 or len(turns)!=1: raise ValueError('exact one completed message/turn required')
    usage=turns[0].get('usage') or turns[0].get('turn',{}).get('usage')
    fields=('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')
    if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in fields): raise ValueError('usage required')
    idx=msgs[0][0]
    if idx>=len(arrivals) or type(arrivals[idx]) is not int or arrivals[idx]<started_ns: raise ValueError('arrival required')
    return {'usage':{k:usage[k] for k in fields},'agent_message_arrival_ns':arrivals[idx],'wall_to_message_ns':arrivals[idx]-started_ns}
