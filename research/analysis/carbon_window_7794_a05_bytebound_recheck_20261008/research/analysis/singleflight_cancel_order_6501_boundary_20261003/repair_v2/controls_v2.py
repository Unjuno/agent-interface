"""Eight legacy controls plus six typed/scope reviewer-style counterexamples."""
import copy
import json

def mutations(raw):
    values=[]
    def add(name,fn):
        v=copy.deepcopy(raw);fn(v)
        assert json.dumps(v,sort_keys=True,separators=(',',':'))!=json.dumps(raw,sort_keys=True,separators=(',',':')),name
        values.append((name,v))
    add('omit',lambda r:r['rows'].pop())
    add('duplicate',lambda r:r['rows'].__setitem__(1,copy.deepcopy(r['rows'][0])))
    add('truth',lambda r:r['rows'][0].__setitem__('truth','FALSE'))
    add('clock',lambda r:r['rows'][0]['events'][0].__setitem__(1,r['rows'][0]['events'][0][1]+1))
    add('order',lambda r:r['rows'][0]['events'][0].__setitem__(2,r['rows'][0]['events'][0][2]+1))
    add('scope',lambda r:r['rows'][0]['outcomes'].__setitem__('foreign',r['rows'][0]['outcomes'].pop('a')))
    add('verdict',lambda r:r['rows'][0]['outcomes']['a'].__setitem__('ordered','CANCELLED_WAITER'))
    add('source',lambda r:r.__setitem__('source_sha256','0'*64))
    add('id-zero-to-false',lambda r:r['rows'][0].__setitem__('id',False))
    add('id-one-to-true',lambda r:r['rows'][1].__setitem__('id',True))
    add('event-clock-to-float',lambda r:r['rows'][0]['events'][0].__setitem__(1,float(r['rows'][0]['events'][0][1])))
    add('event-rank-to-float',lambda r:r['rows'][0]['events'][0].__setitem__(2,float(r['rows'][0]['events'][0][2])))
    add('extra-foreign-caller',lambda r:r['rows'][0]['outcomes'].__setitem__('foreign',copy.deepcopy(r['rows'][0]['outcomes']['a'])))
    add('extra-row-field',lambda r:r['rows'][0].__setitem__('foreign_state','UNDECLARED'))
    return values
