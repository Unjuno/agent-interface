"""Verify fallback preservation and no second frame after failed output."""
import io
import json
import hashlib
from pathlib import Path
from presentation_choice_v1 import choose, deliver
from composed_result_v1 import decode
from shared_result_v1 import canonical

HERE=Path(__file__).resolve().parent;root=HERE/'results/presentation-choice-01';root.mkdir(exist_ok=False)
data=(HERE/'results/inkscape-composed-live-01/invalid/result.json').read_bytes()
original=json.loads(data);rows=[]

def crash(_):raise RuntimeError('injected formatter failure')

for name,source,composer,decoder in [
    ('normal',data,None,None),('no-benefit',b'{"error":"unknown","success":false}',None,None),
    ('formatter-error',data,crash,None),('wrong-reconstruction',data,None,lambda _: {})]:
    kwargs={}
    if composer:kwargs['composer']=composer
    if decoder:kwargs['decoder']=decoder
    stream=io.BytesIO();deliver(source,stream,root/name,**kwargs)
    value=json.loads(stream.getvalue());expected=json.loads(source)
    choice=json.loads((root/name/'choice.json').read_text())
    if choice['choice']=='composed':restored=decode(value)
    elif choice['choice']=='original_with_presentation_error':
        restored=value['result'];assert value['presentation_error']
    else:restored=value
    assert canonical(restored)==canonical(expected)
    assert stream.getvalue()==(root/name/'emission/payload.bin').read_bytes()
    rows.append(dict(name=name,choice=choice,passed=True))

class Broken(io.BytesIO):
    def __init__(self):super().__init__();self.calls=0
    def write(self,b):
        self.calls+=1
        if self.calls==1:return super().write(b[:7])
        raise BrokenPipeError('injected partial write')

stream=Broken()
try:deliver(data,stream,root/'broken-output')
except BrokenPipeError:pass
else:raise AssertionError('write error swallowed')
assert stream.calls==2 and len(stream.getvalue())==7
receipt=json.loads((root/'broken-output/emission/receipt.json').read_text())
assert receipt['status']=='failed' and receipt['accepted_bytes']==7
assert len(list((root/'broken-output').glob('emission')))==1
for invalid in [b'{"a":1,"a":2}',b'{"a":NaN}']:
    try:choose(invalid)
    except ValueError:pass
    else:raise AssertionError('invalid source converted into success')
report=dict(passed=True,controls=rows,partial_write_calls=stream.calls,invalid_sources_rejected=2,
    sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in
             ['presentation_choice_v1.py','probe_presentation_choice_v1.py']},
    scope='Archived operation result plus stream fault injection; no new GUI operation or model call.')
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,controls=len(rows),partial_write_calls=stream.calls)))
