"""Validate oracle against retained files and explicit semantic mutations."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from rectangle_oracle import evaluate,SVG
HERE=Path(__file__).resolve().parent;out=HERE/'results/rectangle-oracle-01';out.mkdir(exist_ok=False)
contract={'target_id':'target','required_dx_screen':12,'pixels_per_svg_unit':1.18,'tolerance_screen':1}
rows=[];sources=[Path(__file__),HERE/'rectangle_oracle.py']
for n,color,expected in [(2,'blue',True),(2,'red',False),(3,'blue',False),(5,'blue',True),(6,'blue',True)]:
    root=HERE/f'results/servo-distractor-{n:02d}'/color;before=root/'fixture.svg';after=root/'shape.svg';sources.extend([before,after])
    result=evaluate(before.read_text(),after.read_text(),contract);assert result['success']==expected
    rows.append(dict(case=f'historical_{n}_{color}',result=result))
root=HERE/'results/servo-distractor-06/blue';before=(root/'fixture.svg').read_text();after=(root/'shape.svg').read_text()
for name in ('unchanged','distractor_color','target_color','opacity','distractor_x','target_width','reorder','extra_rect','viewbox','unsupported_style','duplicate_id'):
    tree=ET.fromstring(after);rects=tree.findall(SVG+'rect')
    if name=='distractor_color':rects[1].set('fill','green')
    elif name=='target_color':rects[0].set('fill','blue')
    elif name=='opacity':rects[1].set('opacity','.5')
    elif name=='distractor_x':rects[1].set('x','80')
    elif name=='target_width':rects[0].set('width','13')
    elif name=='reorder':tree.remove(rects[0]);tree.append(rects[0])
    elif name=='extra_rect':ET.SubElement(tree,SVG+'rect',id='extra',x='0',y='0',width='1',height='1')
    elif name=='viewbox':tree.set('viewBox','0 0 201 200')
    elif name=='unsupported_style':rects[1].set('style','filter:blur(1px)')
    elif name=='duplicate_id':rects[1].set('id','target')
    mutated=before if name=='unchanged' else ET.tostring(tree,encoding='unicode')
    result=evaluate(before,mutated,contract);assert not result['success'],name
    (out/(name+'.svg')).write_text(mutated)
    rows.append(dict(case=name,result=result))
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
print(json.dumps(rows,indent=2))
