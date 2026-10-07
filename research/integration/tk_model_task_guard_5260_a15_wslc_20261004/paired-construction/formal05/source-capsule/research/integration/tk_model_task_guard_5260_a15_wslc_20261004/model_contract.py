"""Model response validation; no task or input authority."""
import json
def parse(rows):
    threads=[r['thread_id'] for r in rows if r.get('type')=='thread.started']
    turns=[r for r in rows if r.get('type')=='turn.completed']
    messages=[r['item']['text'] for r in rows if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='agent_message']
    forbidden=[r for r in rows if r.get('type') in ('error','turn.failed') or
        r.get('type','').startswith('item.') and r.get('item',{}).get('type') not in ('agent_message','reasoning')]
    if len(threads)!=1 or len(turns)!=1 or len(messages)!=1 or forbidden:raise ValueError('model completion or tool use')
    usage=turns[0]['usage']
    required={'input_tokens','cached_input_tokens','output_tokens'}
    known=required|{'cache_write_input_tokens','reasoning_output_tokens'}
    if not required<=set(usage)<=known or any(type(v) is not int or v<0 for v in usage.values()) or usage['cached_input_tokens']>usage['input_tokens']:raise ValueError('usage')
    answer=json.loads(messages[0])
    if (set(answer)!={'decision','observed_target','observed_decoy','prefix'} or
        answer['decision'] not in ('NO_REPAIR','INSERT_PREFIX','REFUSE') or
        any(type(v) is not str for v in answer.values()) or
        answer['decision']!='INSERT_PREFIX' and answer['prefix']!='' or
        answer['decision']=='INSERT_PREFIX' and len(answer['prefix'])!=1):raise ValueError('answer schema')
    return {'answer':answer,'usage':usage,'call_id':threads[0]}
