"""Session-scoped received-event continuation; historical evidence, no input authority."""
import copy,hashlib,json

def digest(record):return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def start(session):
 if type(session) is not str or not session or len(session)>512:raise ValueError('bounded session identity required')
 return {'format':'received-continuation-v1','session':session,'cursor':0,'record_hashes':[],
         'observation':None,'observation_cursor':None,'pending_clock':None,'clocks':{},'channel_closed':False,'authority':'none'}

def advance(state,session,after,reply):
 if state['format']!='received-continuation-v1' or state['session']!=session:raise ValueError('session mismatch')
 if state['authority']!='none' or len(state['record_hashes'])!=state['cursor']:raise ValueError('invalid continuation')
 if type(after) is not int or not 0<=after<=state['cursor']:raise ValueError('unavailable starting cursor')
 if reply.get('status') not in ('boundary','timeout','batch_limit','closed'):raise ValueError('unresolved reply status')
 records=reply['records'];end=reply['cursor']
 if type(records) is not list or type(end) is not int or end!=after+len(records) or end>4096:raise ValueError('noncontiguous or excessive reply')
 hashes=[digest(e) for e in records]
 for index,h in enumerate(hashes,after):
  if index<state['cursor'] and state['record_hashes'][index]!=h:raise ValueError('conflicting replay')
 result=copy.deepcopy(state)
 for index,(e,h) in enumerate(zip(records,hashes),after+1):
  if index<=state['cursor']:continue
  if result['channel_closed']:raise ValueError('new records after closed channel')
  result['record_hashes'].append(h);result['cursor']=index
  if e.get('event')=='observation':
   if type(e.get('sequence')) is not int or e['sequence']<1:raise ValueError('invalid observation sequence')
   if result['observation'] and e['sequence']<=result['observation']['sequence']:raise ValueError('nonincreasing observation')
   result['observation']=copy.deepcopy(e);result['observation_cursor']=index
  if e.get('event')=='command':
   c=e.get('command',{});identifier=c.get('transport_request_id')
   result['pending_clock']={'request_id':identifier,'echo_cursor':index} if c.get('op')=='clock' and type(identifier) is str and identifier else None
  elif e.get('event')=='clock':
   pending=result['pending_clock'];result['pending_clock']=None
   if pending:
    if type(e.get('runtime_ns')) is not int or e['runtime_ns']<=0 or type(e.get('sequence')) is not int:raise ValueError('invalid clock')
    identifier=pending['request_id']
    if identifier in result['clocks']:raise ValueError('duplicate clock echo')
    result['clocks'][identifier]={'record':copy.deepcopy(e),'echo_cursor':pending['echo_cursor'],'record_cursor':index}
 if reply['status']=='closed':result['channel_closed']=True
 return result

def clock_for(state,request_id):
 """Return only the clock correlated with this request, never the first old clock."""
 return copy.deepcopy(state['clocks'].get(request_id))

def read_request(state,events,timeout=2):
 if state['channel_closed']:raise ValueError('channel closed; runtime status remains separately unknown')
 return {'after':state['cursor'],'events':list(events),'timeout':timeout}
