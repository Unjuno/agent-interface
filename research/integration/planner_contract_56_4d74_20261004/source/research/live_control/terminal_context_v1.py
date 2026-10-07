"""Optional lossy planner presentation; complete raw history remains in caller evidence.

Only known terminal schema is shortened. Unknown/malformed records fall back whole.
No authority, task-success inference, or input-generation behavior.
"""
import copy


def present(previous):
    full=copy.deepcopy(previous)
    if previous is None:return full
    try:
        if set(previous)!={'proposal','resolution'}:return full
        r=previous['resolution']
        if set(r)!={'request_id','terminal','authority'} or r['authority']!='none':return full
        t=r['terminal']
        if set(t)!={'event','id','status','error','steps_completed','release','interruption','decision_reason','post_release_observation','terminal_ns','semantic_completion','emit_started_ns'}:return full
        if t['event']!='terminal' or t['status'] not in ('completed','needs_decision','cancelled','expired','failed'):return full
        for key in ('terminal_ns','emit_started_ns'):
            if type(t[key]) is not int or t[key]<0:return full
        def known_release(record):
            if set(record)!={'event','reason','verified','buttons_down','keys_down','verified_ns','valid_until_ns'}:return False
            if record['event']!='owner_release' or type(record['verified']) is not bool:return False
            if type(record['buttons_down']) is not list or type(record['keys_down']) is not list:return False
            if type(record['verified_ns']) is not int or record['verified_ns']<0:return False
            if record['valid_until_ns'] is not None and (type(record['valid_until_ns']) is not int or record['valid_until_ns']<0):return False
            return True
        if not known_release(t['release']):return full
        if t['interruption'] is not None:
            if set(t['interruption'])!={'intent_token','record'} or not known_release(t['interruption']['record']):return full
        post=t['post_release_observation']
        if post is not None:
            if set(post)!={'captures','sequences','equal_sample_pair','error','stopped','authority','scope','elapsed_ms'}:return full
            if type(post['elapsed_ms']) not in (int,float) or not 0<=post['elapsed_ms']<float('inf'):return full
        view=copy.deepcopy(previous);out=view['resolution'];out.pop('request_id')
        terminal=out['terminal']
        for key in ('id','terminal_ns','emit_started_ns'):terminal.pop(key)
        for record in [terminal['release']]+([terminal['interruption']['record']] if terminal['interruption'] else []):
            record.pop('verified_ns');record.pop('valid_until_ns')
        if terminal['interruption']:terminal['interruption'].pop('intent_token')
        if terminal['post_release_observation']:terminal['post_release_observation'].pop('elapsed_ms')
        return view
    except (TypeError,KeyError,ValueError):return full
