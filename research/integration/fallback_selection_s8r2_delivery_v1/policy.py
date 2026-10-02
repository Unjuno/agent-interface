"""A read-only selection assessor, not a source of input authority."""
import json
import sys

FIELDS={'scope','widget_id','generation','seq','text','caret','selection','editable','focus','key_releases'}
EXPECTED={'scope','widget_id','generation','min_seq','original_text'}

def decide(packet):
    out={'grants_action_authority':False,'decision':'YIELD_INVALID_EVIDENCE'}
    if not isinstance(packet,dict) or set(packet)!={'phase','evidence','expected','refinements_used'}:
        return out
    ev,ex=packet['evidence'],packet['expected']
    if not isinstance(ev,dict) or set(ev)!=FIELDS or not isinstance(ex,dict) or set(ex)!=EXPECTED:
        return out
    if packet['phase'] not in ['prepare','assess'] or type(packet['refinements_used']) is not int or packet['refinements_used'] not in [0,1]:
        return out
    if not isinstance(ev['scope'],str) or not ev['scope'] or not isinstance(ex['scope'],str):
        return out
    if any(type(ev[k]) is not int for k in ['widget_id','generation','seq','caret','key_releases']):
        return out
    if any(type(ex[k]) is not int for k in ['widget_id','generation','min_seq']):
        return out
    if not isinstance(ev['text'],str) or not isinstance(ex['original_text'],str) or type(ev['editable']) is not bool:
        return out
    if ev['widget_id']<=0 or ev['generation']<=0 or ev['seq']<0 or ev['key_releases']<0 or not 0<=ev['caret']<=len(ev['text']):
        return out
    s=ev['selection']
    if s is not None and (not isinstance(s,list) or len(s)!=2 or any(type(x)is not int for x in s) or not 0<=s[0]<=s[1]<=len(ev['text'])):
        return out
    if any(ev[k]!=ex[k] for k in ['scope','widget_id','generation']) or ev['seq']<ex['min_seq']:
        out['decision']='YIELD_IDENTITY_OR_ORDER'; return out
    if type(ev['focus']) is not int or ev['focus']!=ev['widget_id'] or not ev['editable']:
        out['decision']='YIELD_NOT_EDITABLE_OR_FOCUSED'; return out
    if ev['text']!=ex['original_text']:
        out['decision']='YIELD_CONTENT_CHANGED'; return out
    if packet['phase']=='prepare':
        out['decision']='SELECT_LINE_ELIGIBLE'
    elif ev['text']=='' or s==[0,len(ev['text'])]:
        out['decision']='REPLACE_ELIGIBLE'
    elif packet['refinements_used']==0:
        out['decision']='REFINE_DOCUMENT_SELECTION'
    else:
        out['decision']='YIELD_SELECTION_INCOMPLETE'
    return out

if __name__=='__main__':
    try:
        obj=json.loads(sys.stdin.read())
        print(json.dumps(decide(obj),sort_keys=True))
    except (ValueError,TypeError) as exc:
        print(json.dumps({'decision':'YIELD_INVALID_EVIDENCE','grants_action_authority':False}))
