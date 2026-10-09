import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit',HERE/'audit.py')
auditmod=importlib.util.module_from_spec(spec); spec.loader.exec_module(auditmod)

class AuditGateTests(unittest.TestCase):
    def make_inputs(self, root, bad=None):
        out=root/'results'; out.mkdir()
        private=root/'private'; private.mkdir()
        gold=json.loads(Path('/private/tmp/agent-interface-8574-pbr-private/gold.json').read_text())
        (private/'gold.json').write_text(json.dumps(gold))
        packet=json.loads((HERE/'blind_packet_order_a.json').read_text())
        (root/'blind_packet_order_a.json').write_text(json.dumps(packet))
        (root/'blind_packet_order_b.json').write_text(json.dumps(list(reversed(packet))))
        (root/'FREEZE.json').write_text('{}')
        ids=[('RV17','checklist','A'),('RV62','freeform','A'),('RV04','perspective','A'),('RV39','checklist','B'),('RV28','freeform','B'),('RV75','perspective','B')]
        reviewers=[]; adj=[]
        cross=next(x['case_id'] for x in gold if x['cross_clause_relations'])
        ambiguous={x['case_id'] for x in gold if x['gold_class']=='ambiguous'}
        for rid,arm,order in ids:
            reviewers.append({'reviewer_id':rid,'arm':arm,'packet_order':order})
            cases=[]
            chosen=(rid=='RV04' and arm=='perspective')
            chosen2=(rid=='RV75' and arm=='perspective')
            for item in (packet if order=='A' else list(reversed(packet))):
                cid=item['case_id']; findings=[]
                if chosen and cid==cross or chosen2 and cid==cross:
                    findings=[{'classification':'SOURCE_SUPPORTED_OMISSION','finding':'Same target identity must be preserved across views.','source_support':'same record ID','verification_gap_or_extra':'No cross-view identity binding.','confidence':0.9}]
                    adj.append({'reviewer_id':rid,'case_id':cid,'finding_index':0,'decision':'SOURCE_SUPPORTED_OMISSION','cross_invariant_match':True,'rationale':'source linkage'})
                cases.append({'case_id':cid,'case_disposition':'AMBIGUOUS_SOURCE' if cid in ambiguous else ('SOURCE_SUPPORTED_OMISSION' if findings else 'NO_DEFECT'),'findings':findings})
            if bad=='missing' and rid=='RV17': cases.pop()
            if bad=='ambiguity' and rid=='RV17':
                target=next(x for x in cases if x['case_id'] in ambiguous); target['case_disposition']='SOURCE_SUPPORTED_OMISSION'
            (out/f'raw_review_{rid}.json').write_text(json.dumps({'reviewer_id':rid,'cases':cases}))
        (out/'assignment_manifest.json').write_text(json.dumps({'reviewers':reviewers}))
        (out/'adjudicated_blind.json').write_text(json.dumps({'items':adj}))
        return out,private
    def test_scoped_incremental_rescue(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); out,private=self.make_inputs(root)
            result=auditmod.audit(root,out,private)
            self.assertEqual(result['status'],'PASS_METHOD_SCOPED')
    def test_missing_case_fails_audit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); out,private=self.make_inputs(root,'missing')
            self.assertEqual(auditmod.audit(root,out,private)['status'],'FAIL_AUDIT_OR_METHOD')
    def test_forced_ambiguity_fails_method(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); out,private=self.make_inputs(root,'ambiguity')
            self.assertEqual(auditmod.audit(root,out,private)['status'],'FAIL_AUDIT_OR_METHOD')

if __name__=='__main__': unittest.main()
