"""Development-known focus negatives and earlier real modal images."""
import hashlib,json
from pathlib import Path
from PIL import Image
from modal_visual_predicate import ModalVisualPredicate
HERE=Path(__file__).resolve().parent;out=HERE/'results/modal-predicate-01';out.mkdir(exist_ok=False)
source=HERE/'results/modal-focus-01/tab-0.png'
config=dict(modal_box=[385,302,509,195],action_box=[696,450,178,27],max_error=.03)
predicate=ModalVisualPredicate(Image.open(source).convert('RGB'),**config)
cases=[(f'focus_{i}',HERE/f'results/modal-focus-01/tab-{i}.png',i in (0,3)) for i in range(4)]
cases += [('historical_1',HERE/'results/journal-calc-01/007.png',True),('historical_2',HERE/'results/journal-calc-02/006.png',True),('historical_3',HERE/'results/final-score-calc-01/006.png',True),('initial',HERE/'results/journal-calc-02/001.png',False),('saved',HERE/'results/journal-calc-02/015.png',False)]
rows=[]
for name,path,expected in cases:
    r=predicate.inspect(Image.open(path).convert('RGB'))
    assert (r['status']=='visual_candidate')==expected,name
    rows.append(dict(case=name,expected_candidate=expected,modal_only_candidate=r['modal_error']<=.03,result=r))
assert rows[1]['modal_only_candidate'] and rows[2]['modal_only_candidate']
assert predicate.inspect(Image.new('RGB',(1,1)))['status']=='unsupported_frame'
(out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
paths=[Path(__file__),HERE/'modal_visual_predicate.py',source]+[path for _,path,_ in cases]
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
print(json.dumps(rows,indent=2))
