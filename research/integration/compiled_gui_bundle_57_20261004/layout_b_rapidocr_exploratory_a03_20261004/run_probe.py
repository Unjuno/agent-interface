from __future__ import annotations
import hashlib, json, subprocess, tempfile, time
from pathlib import Path
from PIL import Image
import numpy as np
from rapidocr import RapidOCR

repo=next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())
a02=repo/'research/integration/compiled_gui_bundle_57_20261004/layout_b_ocr_construction_a02_20261004/RAW.json'
src=json.loads(a02.read_text())
rows=src['heldout_rows']
engine=RapidOCR()
sha=lambda b:hashlib.sha256(b).hexdigest()
start=time.perf_counter_ns()
out=[]
with tempfile.TemporaryDirectory(prefix='rapidocr-a03-', dir=repo/'work') as td:
    td=Path(td)
    for i,row in enumerate(rows):
        frame=repo/row['frame']
        if sha(frame.read_bytes()) != row['frame_sha256']:
            raise RuntimeError(f"source hash mismatch: {row['frame']}")
        crop=td/f'{i:03}.png'
        cmd=['magick',str(frame),'-crop','280x26+499+546','+repage','-alpha','remove','-colorspace','Gray','-resize','800%','-bordercolor','white','-border','32',str(crop)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        if p.returncode: raise RuntimeError(p.stderr)
        pixels=subprocess.run(['magick',str(crop),'-colorspace','Gray','-depth','8','gray:-'],capture_output=True)
        if pixels.returncode: raise RuntimeError(p.stderr.decode(errors='replace'))
        im=Image.open(crop).convert('RGB')
        res=engine(np.asarray(im))
        texts=list(res.txts or [])
        joined=''.join(texts)
        out.append({'arm':row['arm'],'task_id':row['task_id'],'frame':row['frame'],'frame_sha256':row['frame_sha256'],'crop_pixel_sha256':sha(pixels.stdout),'expected_token':row['expected_token'],'rapidocr_texts':texts,'joined_text':joined,'exact_match':joined.strip()==row['expected_token'],'is_task_source_frame':row.get('is_task_source_frame',False),'rapidocr_elapsed_s':res.elapse})
elapsed=time.perf_counter_ns()-start
model_dir=Path(__import__('rapidocr').__file__).resolve().parent/'models'
models=[{'file':p.name,'sha256':sha(p.read_bytes()),'size_bytes':p.stat().st_size} for p in sorted(model_dir.glob('*.onnx'))]
report={'model_files':models,'experiment_id':'layout_b_rapidocr_exploratory_a03_20261004','classification':'EXPLORATORY_ONLY_RETROSPECTIVE_REPLAY_NOT_QUALIFYING','host':'Darwin ARM64','runtime':'RapidOCR 3.9.2 + ONNX Runtime CPU 1.30.0','engine_defaults':'PP-OCRv6 det_small, PP-OCRv6 rec_small, ch_ppocr_mobile_v2.0_cls_mobile; no custom words, no character normalization','input':'A02 frozen crop recipe, all 56 previously examined plain/persistent task4-6 frames','criterion':'exact concatenated recognized text after outer whitespace strip; source frames must be negative; task/arm pass requires any exact frame','elapsed_ns':elapsed,'rows':out}
base=Path(__file__).resolve().parent
base.mkdir(parents=True,exist_ok=True)
(base/'RAW.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
from collections import defaultdict
cases=defaultdict(list)
for r in out: cases[(r['arm'],r['task_id'])].append(r)
summary={f'{a}/{t}':{'frames':len(v),'exact_frames':[r['frame'].rsplit('/',1)[-1] for r in v if r['exact_match']],'source_exact_frames':[r['frame'].rsplit('/',1)[-1] for r in v if r['is_task_source_frame'] and r['exact_match']],'outputs':sorted(set(r['joined_text'] for r in v))} for (a,t),v in cases.items()}
(base/'SUMMARY.json').write_text(json.dumps({'classification':report['classification'],'case_summary':summary},indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'elapsed_ns':elapsed,'case_summary':summary},indent=2,ensure_ascii=False))
