from model import *
from oracle import decide

def eps(adapter,rev=0):
    return {f'rel.{r}':f'{adapter}:{r}:{rev}' for r in RELATIONS}

def main():
    m=semantic_manifest(); h=canonical_hash(m); e=eps('a',0); b=binding('agent-interface',1,1,'a',e)
    checks={}
    checks['stable']=resolve(m,'agent-interface',1,1,b,'control')==('BOUND','a:control:0')
    b2=binding('agent-interface',1,2,'a',eps('a',1))
    checks['stale_epoch']=resolve(m,'agent-interface',1,2,b,'control')==('DISCOVER_BINDING',None)
    checks['rotated_current']=resolve(m,'agent-interface',1,2,b2,'control')==('BOUND','a:control:1')
    b3=binding('agent-interface',1,3,'b',eps('b',0))
    checks['adapter_switch']=resolve(m,'agent-interface',1,3,b3,'observation')==('BOUND','b:observation:0') and canonical_hash(m)==h
    bad=binding('other',1,3,'b',eps('b',0));checks['wrong_service']=resolve(m,'agent-interface',1,3,bad,'control')[0]=='DISCOVER_BINDING'
    bad=binding('agent-interface',2,3,'b',eps('b',0));checks['wrong_protocol']=resolve(m,'agent-interface',1,3,bad,'control')[0]=='DISCOVER_BINDING'
    em=eps('b',0); em.pop('rel.control'); fb=binding('agent-interface',1,3,'b',em);checks['fallback']=resolve(m,'agent-interface',1,3,fb,'control')==('FALLBACK','b:fallback:0')
    em=eps('b',0); em.pop('rel.control'); em.pop('rel.fallback'); fb=binding('agent-interface',1,3,'b',em);checks['missing_fallback']=resolve(m,'agent-interface',1,3,fb,'control')[0]=='BINDING_INCOMPLETE'
    mm=semantic_manifest();mm['relations'].pop('control');checks['manifest_missing_relation']=resolve(mm,'agent-interface',1,3,b3,'control')[0]=='MANIFEST_INCOMPLETE'
    em=eps('b',0);em['rel.control']='bad\nendpoint';bb=binding('agent-interface',1,3,'b',em);checks['malformed_endpoint']=resolve(m,'agent-interface',1,3,bb,'control')==('FALLBACK','b:fallback:0')
    checks['oracle']=all(resolve(m,'agent-interface',1,3,b3,r)==decide(m,'agent-interface',1,3,b3,r) for r in RELATIONS[:-1])
    print(checks)
    assert all(checks.values())
if __name__=='__main__':main()
