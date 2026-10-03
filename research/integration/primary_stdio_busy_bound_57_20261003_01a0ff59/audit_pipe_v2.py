"""Raw-only exact lifecycle reconstruction. Imports no producer or runtime."""
import json, sys
from pathlib import Path

def require(value,message):
    if not value: raise ValueError(message)
def same(a,b):
    return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def audit(root):
    root=Path(root)
    reports=[]
    for arm,busy,code,statuses in [('baseline',2,0,['ready','busy','busy','returned','terminal']),('candidate',1,2,['ready','busy','returned'])]:
        p=root/arm
        read=lambda name:json.loads((p/name).read_text())
        lines=lambda name:[json.loads(line) for line in (p/name).read_text().splitlines()]
        process=read('process.json')
        require(same(process['exit'],{'code':code,'signal':None}) and process['ready_observed'] is True,'owner exit/readiness')
        require(process['platform']=='win32' and process['node']=='v24.19.0','declared environment')
        commands=lines('stdin.jsonl')
        require(same(commands,[{'id':i,'method':'call','args':['interface_close',{}]} for i in (1,2,3)]),'input schedule')
        rows=lines('stdout.jsonl')
        require([row['status'] for row in rows]==statuses,'owner response order/cardinality')
        require(all(row['schema']=='agent-interface/primary-stdio-v1' for row in rows),'owner schema')
        refusals=[row for row in rows if row['status']=='busy']
        require(len(refusals)==busy and all(same(row,{'schema':'agent-interface/primary-stdio-v1','status':'busy','operation_invoked':False,'pending':True,'next_id':2}) for row in refusals),'busy contract')
        require(same(read('host/exit.json'),{'code':0,'signal':None}),'same relay terminal')
        request={'id':1,'tool':'interface_close','arguments':{}}
        require(same(lines('relay-received.jsonl'),[request]),'actual relay dispatch count/identity')
        require(same(read('host/request-1.json'),request),'retained request')
        require(sorted(x.name for x in (p/'host').glob('request-*.json'))==['request-1.json'],'no later relay request')
        require(sorted(x.name for x in (p/'exchange').glob('request-*.json'))==['request-1.json'],'no later primary command')
        require(same(read('exchange/request-1.json'),commands[0]),'consumed command')
        presentation=read('exchange/presentation-1.json')
        result=next(row['result'] for row in rows if row['status']=='returned')
        require(same(result,presentation) and type(result['id']) is int and result['id']==1 and type(result['next_id']) is int and result['next_id']==2,'exact returned presentation')
        reply=read('host/reply-1.json')
        original=read('exchange/original-reply-1.json')
        require(same(original.pop('attempt'),1) and same(original,reply),'original reply identity')
        require(same(reply,{'id':1,'tool':'interface_close','status':'returned','next_id':2,'result':{'isError':False,'content':[{'type':'text','text':'{"status":"closed"}'}]}}),'exact fixture outcome')
        require(result['images']==[] and result['presented_text'][-1]=='{"status":"closed"}','text result preserved')
        events=lines('host/host-events.jsonl')
        require([row['kind'] for row in events]==['send_requested','reply_available','presentation_started','presentation_callbacks_completed','transport_closed'],'same transport lifetime')
        require(same([row['sequence'] for row in events],[1,2,3,4,5]),'event order')
        if arm=='candidate':
            require((p/'stderr.txt').read_text().strip()=='Error: primary busy response backlog','overload owner error')
        else:require((p/'stderr.txt').read_bytes()==b'' and same(rows[-1]['exit'],{'code':0,'signal':None}),'baseline normal terminal')
        reports.append({'arm':arm,'busy_responses':busy,'committed_commands':1,'relay_requests':1,'returned_presentations':1,'relay_exit_code':0,'owner_exit_code':code})
    return {'result':'PASS_PRIMARY_OVERLOAD_OWNER_SCOPED','arms':reports,'limitations':['fixture reply, not OS input/effect','local Windows child pipes only','no permanently blocked output or command deadline','no performance/model token claim']}

if __name__=='__main__':
    print(json.dumps(audit(Path(sys.argv[1])),sort_keys=True))
