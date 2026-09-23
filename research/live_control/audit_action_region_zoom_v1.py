"""Audit exact construction of an action-region zoom presentation."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('run_root',type=Path);parser.add_argument('artifact',type=Path);args=parser.parse_args();manifest=json.loads((args.artifact/'manifest.json').read_text());assert manifest['format']=='action-region-zoom-v1' and manifest['scope'].startswith('archived visual-only')
    typed=args.run_root/f"typed-{manifest['turn']}.json";applied=args.run_root/f"applied-{manifest['turn']}.json";record=json.loads(applied.read_text());runtime=args.run_root/'runtime';before=runtime/Path(record['source_observation']['image']).name;after=runtime/Path(record['result']['state']['continuation']['observation']['image']).name
    assert manifest['sources']['script_sha256']==sha(Path(__file__).with_name('action_region_zoom_v1.py')) and manifest['sources']['typed_sha256']==sha(typed) and manifest['sources']['applied_sha256']==sha(applied) and manifest['sources']['before_sha256']==sha(before) and manifest['sources']['after_sha256']==sha(after)
    output=args.artifact/manifest['output']['path'];assert sha(output)==manifest['output']['sha256'] and output.stat().st_size==manifest['output']['bytes']
    with Image.open(after) as current,Image.open(output) as presentation:
        current=current.convert('RGB');presentation=presentation.convert('RGB');assert presentation.size==tuple(manifest['presentation_dimensions']) and presentation.crop((0,0,current.width,current.height)).tobytes()==current.tobytes()
        assert manifest['full_frame_rows']==current.height and manifest['presentation_dimensions'][1]>current.height
    source=Path(__file__).with_name('action_region_zoom_v1.py').read_text()
    for token in ('guarded_l_score','evaluation.json','changed_surrounding_tiles','target_tiles'):assert token not in source
    print(json.dumps({'audit_passed':True,'visual_only':True,'full_after_preserved_exactly':True,'crop_box':manifest['crop_box'],'presentation_dimensions':manifest['presentation_dimensions'],'output_bytes':manifest['output']['bytes']},indent=2))
if __name__=='__main__':main()
