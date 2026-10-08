"""Narrow event selection retaining complete latest observation and terminal."""
import copy,hashlib,json

def build(reply):
 records=reply['records'];terminals=[e for e in records if e.get('event')=='terminal']
 if len(terminals)!=1:raise ValueError('one terminal required')
 terminal=terminals[0];identifier=terminal['id']
 observations=[e for e in records if e.get('event')=='observation']
 if not observations or any(e.get('id')!=identifier for e in observations):raise ValueError('one observed action required')
 seq=[e['sequence'] for e in observations]
 if any(type(n) is not int for n in seq) or seq!=sorted(set(seq)):raise ValueError('strictly increasing observation sequences required')
 if records.index(observations[-1])>records.index(terminal):raise ValueError('observation after terminal')
 return {'format':'focus-decision-view-v2','scope':'lossy event selection for explicit focus questions; full latest records preserved, omitted earlier history available at source',
 'source_sha256':hashlib.sha256(json.dumps(reply,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
 'cursor':reply['cursor'],'terminal':copy.deepcopy(terminal),'observation':copy.deepcopy(observations[-1])}
