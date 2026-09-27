"""Construction and corruption controls; independent of the scored allocation IDs."""
import copy, json, os, shutil, tempfile, unittest
from pathlib import Path
from experiment import one, dump, NativeGit, inspect_candidate, POLICIES, SCENARIOS, WRITE
from audit import audit_case, audit_all, Objects

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory() if not os.environ.get('TEST_ROOT') else None
        cls.root = Path(os.environ['TEST_ROOT']) if cls.temp is None else Path(cls.temp.name)/'construction'
        cls.root.mkdir(parents=True,exist_ok=False)
        cls.cases=[];cls.results={}
        for scenario in SCENARIOS:
            for policy in POLICIES:
                c=dict(id='unit-'+policy+'-'+scenario,rep=1,scenario=scenario,policy=policy)
                cls.cases.append(c);cls.results[(policy,scenario)]=one(cls.root,c)
        cls.plan=dict(allocation='unit-matrix',cases=cls.cases)
        dump(cls.root/'started.json',{'allocation':'unit-matrix'})
        dump(cls.root/'completed.json',{'count':len(cls.cases)})

    @classmethod
    def tearDownClass(cls):
        if cls.temp: cls.temp.cleanup()

    def cloned(self, scenario='correct', policy='scope_and_postcondition'):
        source=self.root/('unit-'+policy+'-'+scenario)
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        dest=Path(t.name)/source.name;shutil.copytree(source,dest)
        row=json.loads((dest/'result.json').read_text())
        case={k:row[k] for k in ('id','rep','scenario','policy')}
        return dest,row,case

    def bad_row(self,key,value,scenario='correct'):
        d,r,c=self.cloned(scenario);r[key]=value;dump(d/'result.json',r)
        with self.assertRaises(AssertionError): audit_case(d,c)

    def test_matrix(self):
        r=audit_all(self.root,self.plan)
        self.assertEqual(r['summary']['scope_and_postcondition']['correct'],12)
        self.assertEqual(r['summary']['scope_only']['correct'],8)
        self.assertEqual(r['summary']['scope_only']['wrong_publications'],4)

    def test_wrong_effect_types(self):
        for s in ('wrong_bytes','wrong_mode','wrong_kind','target_deleted'):
            with self.subTest(s=s):
                self.assertEqual(self.results[('scope_only',s)]['reason'],'applied')
                self.assertEqual(self.results[('scope_and_postcondition',s)]['reason'],'postcondition_mismatch')

    def test_common_guards(self):
        for s in ('extra_change','no_op','wrong_parent','read_conflict','write_conflict','ref_race'):
            with self.subTest(s=s):
                a=self.results[('scope_only',s)];b=self.results[('scope_and_postcondition',s)]
                self.assertEqual(a['reason'],b['reason']);self.assertNotEqual(a['reason'],'applied')

    def test_corrupt_final(self): self.bad_row('final','0'*40)
    def test_false_reason(self): self.bad_row('reason','applied','wrong_bytes')
    def test_bool_clock(self): self.bad_row('planned_ns',True)
    def test_wrong_returncode(self): self.bad_row('returncode',1)
    def test_reversed_clock(self): self.bad_row('publish_end_ns',0)

    def test_false_postcondition_receipt(self):
        d,r,c=self.cloned('wrong_bytes');r['receipt']['post_ok']=True;dump(d/'result.json',r)
        with self.assertRaises(AssertionError): audit_case(d,c)

    def test_changed_request(self):
        d,r,c=self.cloned();q=json.loads((d/'request.json').read_text());q['after'][WRITE][0]='100755';dump(d/'request.json',q)
        with self.assertRaises(AssertionError): audit_case(d,c)

    def test_object_corruption(self):
        d,r,c=self.cloned();oid=r['candidate'];f=d/'repo.git/objects'/oid[:2]/oid[2:]
        f.chmod(0o644);f.write_bytes(b'not a Git object')
        with self.assertRaises(Exception): audit_case(d,c)

    def test_reflog_corruption(self):
        d,r,c=self.cloned();p=d/'repo.git/logs/refs/heads/target';p.write_text(p.read_text().replace('publish candidate','wrong event'))
        with self.assertRaises(AssertionError): audit_case(d,c)

    def test_publication_receipt_corruption(self):
        d,r,c=self.cloned();p=d/'commands.jsonl';cs=[json.loads(x) for x in p.read_text().splitlines()]
        for x in cs:
            if 'publish candidate' in x['argv']: x['argv'][-1]='0'*40
        p.write_text(''.join(json.dumps(x)+'\n' for x in cs))
        with self.assertRaises(AssertionError): audit_case(d,c)

    def test_incomplete_or_duplicate_plan(self):
        for cases in (self.cases[:-1],self.cases+[self.cases[0]]):
            with self.subTest(n=len(cases)),self.assertRaises(AssertionError):
                audit_all(self.root,dict(self.plan,cases=cases))

    def test_same_id_refused(self):
        with self.assertRaises(FileExistsError): one(self.root,self.cases[0])

    def test_invalid_policy_or_mutable_identity(self):
        d,r,c=self.cloned();g=NativeGit(d);q=json.loads((d/'request.json').read_text())
        with self.assertRaises(ValueError):inspect_candidate(g,q,r['current'],r['candidate'],'unknown')
        with self.assertRaises(ValueError):inspect_candidate(g,q,r['current'],'refs/heads/target','scope_only')

    def test_noop_not_mislabelled_success(self):
        self.assertEqual(self.results[('scope_and_postcondition','no_op')]['reason'],'scope_mismatch')

if __name__=='__main__':unittest.main(verbosity=2)
