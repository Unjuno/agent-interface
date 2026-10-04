"""Explicit fake protocol peer. Never invokes a provider."""
import sys, json
turn = 0
def emit(obj):
    print(json.dumps(obj, separators=(',', ':')), flush=True)
def complete(identifier, status):
    emit({'method':'turn/completed','params':{'threadId':'fake-thread',
          'turn':{'id':identifier,'status':status,'items':[
          {'type':'agentMessage','text':'{"action":"fresh"}'}]}}})
for line in sys.stdin:
    m=json.loads(line); method=m['method']; ident=m.get('id')
    if method=='initialize':emit({'id':ident,'result':{'fake':True}})
    elif method=='initialized':pass
    elif method=='thread/start':emit({'id':ident,'result':{'thread':{'id':'fake-thread'}}})
    elif method=='turn/start':
        turn+=1; t=f'fake-turn-{turn}'
        emit({'id':ident,'result':{'turn':{'id':t}}})
        emit({'method':'turn/started','params':{'threadId':'fake-thread','turn':{'id':t}}})
        if turn==3:complete(t,'completed')
    elif method=='turn/interrupt':
        t=m['params']['turnId'];emit({'id':ident,'result':{}})
        complete(t,'interrupted' if t=='fake-turn-1' else 'completed')
    else:raise ValueError('unexpected fake method '+method)
