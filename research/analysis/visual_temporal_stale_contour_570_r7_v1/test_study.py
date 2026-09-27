from __future__ import annotations
import base64, hashlib, json, tempfile, unittest
from pathlib import Path
from audit import audit, iou, map_box, center_error, expected_mapping
class StudyTests(unittest.TestCase):
    def test_pair_current_pane_inverse(self):
        m={'kind':'current_right_pane_scaled'}
        src=[120,200,300,280]; shown=[640+src[0]/2,40+src[1]*.95,640+src[2]/2,40+src[3]*.95]
        self.assertTrue(all(abs(a-b)<=1 for a,b in zip(map_box(shown,m),src)))
    def test_identity_map_does_not_shift(self):
        self.assertEqual(map_box([1,2,30,40],{'kind':'identity'}),[1,2,30,40])
    def test_iou_exact_and_disjoint(self):
        self.assertEqual(iou([0,0,10,10],[0,0,10,10]),1.0)
        self.assertEqual(iou([0,0,10,10],[20,20,30,30]),0.0)
    def test_center_error(self):
        self.assertEqual(center_error([10,10,30,30],[10,10,30,30]),0.0)
    def fixture(self,root):
        root=Path(root); data=root/'data'; ev=root/'evidence'; formal=ev/'formal'; data.mkdir();formal.mkdir(parents=True)
        pre={'allocation':'visual-temporal-570-stale-contour-r7-20260927-01','prompt':'prompt','prompt_sha256':hashlib.sha256(b'prompt').hexdigest(),'formal_cases':[]}
        now=1000
        for i in range(12):
            cid=f'screen-{i:02d}'; present=i<10; target=[100+i,150,180+i,210] if present else None; stale=[500,500,580,560]
            prior=(cid+' prior').encode(); current=(cid+' current').encode(); (data/f'{cid}-prior.png').write_bytes(prior); (data/f'{cid}-current.png').write_bytes(current)
            for j,arm in enumerate(['CURRENT_RAW','PAIRED_HISTORY','STALE_CONTOUR']):
                case_id=f'{cid}-{arm.lower()}'; mapping={'kind':'identity'} if arm=='CURRENT_RAW' else ({'kind':'current_right_pane_scaled','pane':[640,40,1280,800],'scale':[2.0,800/760]} if arm=='PAIRED_HISTORY' else {'kind':'stale_contour_identity','old_target_box':stale,'outline_color':'#e04b32'})
                image=(case_id+' image').encode(); name=case_id+'.png'; (data/name).write_bytes(image)
                c={'case_id':case_id,'source_case_id':cid,'seed':100+i,'present':present,'arm':arm,'prior_path':f'{cid}-prior.png','prior_sha256':hashlib.sha256(prior).hexdigest(),
                   'current_path':f'{cid}-current.png','current_sha256':hashlib.sha256(current).hexdigest(),'presentation_path':name,'presentation_sha256':hashlib.sha256(image).hexdigest(),
                   'target_box':target,'stale_box':stale,'mapping':mapping,'width':1280,'height':800};pre['formal_cases'].append(c)
                if present:
                    box=target if arm!='PAIRED_HISTORY' else [640+target[0]/2,40+target[1]*.95,640+target[2]/2,40+target[3]*.95]
                    response={'message':{'content':json.dumps({'present':True,'box':box})}}
                else: response={'message':{'content':json.dumps({'present':False,'box':None})}}
                payload={'model':'qwen2.5vl:3b','messages':[{'role':'user','content':'prompt','images':[base64.b64encode(image).decode()]}],'format':'json','stream':False,'keep_alive':'5m','options':{'temperature':0,'seed':c['seed'],'num_predict':128}}
                request_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest();start=now;end=now+100;now+=200
                row={'case_id':case_id,'source_case_id':cid,'arm':arm,'seed':c['seed'],'model':'qwen2.5vl:3b','expected_digest':'fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1',
                     'image_sha256':c['presentation_sha256'],'prior_sha256':c['prior_sha256'],'current_sha256':c['current_sha256'],'prompt_sha256':pre['prompt_sha256'],'request':payload,'request_sha256':request_hash,
                     'started_utc_ns':start,'ended_utc_ns':end,'response':response,'error':None}
                (formal/(case_id+'.json')).write_text(json.dumps(row))
                self._samples.append({'utc_ns':start+50,'memory_used_mib':300,'ollama_ps_stdout':'qwen 100% GPU'})
        pre['formal_cases'].sort(key=lambda c:c['case_id']); raw=json.dumps(pre,sort_keys=True,indent=2)+'\n';(data/'PREFORMAL.json').write_text(raw)
        manifest={'schema':'fixture','artifacts':[]};mb=json.dumps(manifest).encode();(root/'EVIDENCE_MANIFEST.json').write_bytes(mb)
        freeze={'pref_sha256':hashlib.sha256((data/'PREFORMAL.json').read_bytes()).hexdigest(),'source_sha256':{},'evidence_manifest_sha256':hashlib.sha256(mb).hexdigest()};fb=json.dumps(freeze).encode();(root/'FREEZE.json').write_bytes(fb);(root/'FREEZE.sha256').write_text(hashlib.sha256(fb).hexdigest()+'  FREEZE.json\n')
        (ev/'baseline.json').write_text(json.dumps({'memory_used_mib':0}));(ev/'RUN_STATUS.json').write_text(json.dumps({'completed_calls':36,'expected_calls':36,'failure':None,'retries':0}));(ev/'sampler.jsonl').write_text('\n'.join(json.dumps(x) for x in self._samples))
        return root
    def setUp(self): self._samples=[]
    def run_audit(self,root): return audit(Path(root),Path(root)/'AUDIT.json')
    def test_complete_three_arm_audit_has_no_integrity_errors(self):
        with tempfile.TemporaryDirectory() as d:
            result=self.run_audit(self.fixture(d));self.assertEqual(result['errors'],[]);self.assertTrue(result['complete']);self.assertEqual(result['model_calls'],36)
    def test_request_image_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d);p=root/'evidence/formal/screen-00-current_raw.json';r=json.loads(p.read_text());r['request']['messages'][0]['images'][0]=base64.b64encode(b'mutated').decode();p.write_text(json.dumps(r));self.assertIn('request_binding:screen-00-current_raw',self.run_audit(root)['errors'])
    def test_source_pixel_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d);(root/'data/screen-00-current.png').write_bytes(b'changed');self.assertIn('source_hash:screen-00-current_raw',self.run_audit(root)['errors'])
    def test_mapping_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d);p=root/'data/PREFORMAL.json';pre=json.loads(p.read_text());next(c for c in pre['formal_cases'] if c['arm']=='PAIRED_HISTORY')['mapping']['scale'][:]=[4,1];p.write_text(json.dumps(pre));self.assertIn('mapping_contract:screen-00-paired_history',self.run_audit(root)['errors'])
    def test_malformed_model_response_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d);p=root/'evidence/formal/screen-00-current_raw.json';r=json.loads(p.read_text());r['response']['message']['content']='not json';p.write_text(json.dumps(r));self.assertIn('response_schema:screen-00-current_raw',self.run_audit(root)['errors'])
    def test_missing_raw_call_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d);(root/'evidence/formal/screen-00-current_raw.json').unlink();self.assertIn('missing:screen-00-current_raw',self.run_audit(root)['errors'])
    def test_missing_gpu_placement_holds_audit(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d);(root/'evidence/sampler.jsonl').write_text('');r=self.run_audit(root);self.assertIn('gpu_overlap:screen-00-current_raw',r['errors']);self.assertEqual(r['decision'],'HOLD_AUDIT_OR_GPU')
    def test_changed_frozen_manifest_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=self.fixture(d);p=root/'data/PREFORMAL.json';pre=json.loads(p.read_text());pre['prompt']='changed';p.write_text(json.dumps(pre));self.assertIn('freeze_pref_hash',self.run_audit(root)['errors'])
if __name__=='__main__': unittest.main(verbosity=2)
