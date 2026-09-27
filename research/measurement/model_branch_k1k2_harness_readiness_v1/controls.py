import json
from harness import prompt,prompt_diff,parse_answer,extract_jsonl

def must_reject(name,fn,out):
    try: fn(); ok=False
    except Exception: ok=True
    out.append((name,ok))

def main():
    out=[]
    d=prompt_diff();out.append(('prompt_one_byte',d['same_length'] and d['diff_count']==1 and d['bytes']==[(49,50)]))
    k1='{"branches":[{"branch_id":"b1","predicate":"LEFT","semantic_action":"CONTINUE_LEFT","no_authority":true}]}'
    k2='{"branches":[{"branch_id":"b1","predicate":"LEFT","semantic_action":"CONTINUE_LEFT","no_authority":true},{"branch_id":"b2","predicate":"RIGHT","semantic_action":"CONTINUE_RIGHT","no_authority":true}]}'
    out.append(('parse_k1',len(parse_answer(k1,1)['branches'])==1));out.append(('parse_k2',len(parse_answer(k2,2)['branches'])==2))
    must_reject('extra_branch',lambda:parse_answer(k2,1),out)
    must_reject('authority_field',lambda:parse_answer('{"branches":[{"branch_id":"b1","predicate":"L","semantic_action":"YIELD","no_authority":true,"authority":true}]}',1),out)
    lines=[json.dumps({'type':'thread.started'}),json.dumps({'type':'item.completed','item':{'type':'agent_message','text':k1}}),json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':20,'output_tokens':10,'reasoning_output_tokens':0}})]
    z=extract_jsonl(lines,1000,[1100,1200,1300]);out.append(('usage_extract',z['wall_to_message_ns']==200 and z['usage']['output_tokens']==10))
    must_reject('usage_missing',lambda:extract_jsonl(lines[:-1]+[json.dumps({'type':'turn.completed'})],1000,[1100,1200,1300]),out)
    assert all(v for _,v in out),out
    print(json.dumps({'controls':out,'passed':sum(v for _,v in out)},indent=2))
if __name__=='__main__':main()
