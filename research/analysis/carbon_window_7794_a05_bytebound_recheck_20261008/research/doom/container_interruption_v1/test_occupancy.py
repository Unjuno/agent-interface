import copy, random, unittest
from occupancy import analyze_program, EvidenceError, union_ns


def trace(keys=('a',)):
    rows=[{'event':'accepted','id':'p','intent_token':'t','accepted_ns':0}]
    for i,k in enumerate(keys):
        rows.append({'event':'input_admission','key':k,'intent_token':'t','admitted_ns':10+i,'input_ack_ns':20+i})
    for i,k in enumerate(keys):
        rows.append({'event':'input_release_transition','key':k,'operation':'up','intent_token':'t',
                     'release_batch_identifier':'p','transition_schema':'input-release-transition-v3',
                     'release_call_started_ns':80+i,'release_call_returned_ns':90+i,
                     'owner_transition_verified':True,'ordinary_release_candidate':True})
    rows.append({'event':'terminal','id':'p','status':'completed','terminal_ns':100,
                 'interruption':None,'release':{'verified':True,'keys_down':[],'buttons_down':[],
                                               'verified_ns':95,'intent_token':'t'}})
    return rows

class Tests(unittest.TestCase):
    def value(self,rows=None,start=0,end=100):return analyze_program(trace() if rows is None else rows,'p',start,end)
    def test_normal(self):
        r=self.value(); self.assertEqual((r['retained_lower_ns'],r['retained_upper_ns']),(60,80))
    def test_two_keys_union_not_sum(self):
        r=self.value(trace(('a','d')));self.assertEqual((r['retained_lower_ns'],r['retained_upper_ns']),(61,81))
    def test_clip(self):
        r=self.value(start=30,end=60);self.assertEqual((r['retained_lower_ns'],r['retained_upper_ns']),(30,30))
    def test_coast_requires_accepted_terminal(self):
        r=self.value(trace(()));self.assertEqual(r['no_input_lower_ns'],100)
    def test_missing_release_never_becomes_zero(self):
        r=trace();del r[2]
        with self.assertRaises(EvidenceError):self.value(r)
    def test_orphan_release(self):
        r=trace();del r[1]
        with self.assertRaises(EvidenceError):self.value(r)
    def test_duplicate_release(self):
        r=trace();r.insert(3,copy.deepcopy(r[2]))
        with self.assertRaises(EvidenceError):self.value(r)
    def test_duplicate_down(self):
        r=trace();r.insert(2,copy.deepcopy(r[1]))
        with self.assertRaises(EvidenceError):self.value(r)
    def test_negative_clock(self):
        r=trace();r[1]['admitted_ns']=-1
        with self.assertRaises(EvidenceError):self.value(r)
    def test_bool_clock(self):
        r=trace();r[1]['admitted_ns']=True
        with self.assertRaises(EvidenceError):self.value(r)
    def test_inverted_release_clock(self):
        r=trace();r[2]['release_call_returned_ns']=79
        with self.assertRaises(EvidenceError):self.value(r)
    def test_token_mismatch(self):
        r=trace();r[2]['intent_token']='other'
        with self.assertRaises(EvidenceError):self.value(r)
    def test_missing_acceptance(self):
        with self.assertRaises(EvidenceError):self.value(trace()[1:])
    def test_missing_terminal(self):
        with self.assertRaises(EvidenceError):self.value(trace()[:-1])
    def test_unverified_terminal(self):
        r=trace();r[-1]['release']['verified']=False
        with self.assertRaises(EvidenceError):self.value(r)
    def test_cancelled_is_censored_not_zero(self):
        r=trace();r[-1]['status']='cancelled';r[2]['ordinary_release_candidate']=False;r[2]['owner_transition_verified']=False
        r[-1]['interruption']={'intent_token':'t','record':{'verified':True,'keys_down':[],'buttons_down':[], 'verified_ns':70,'reason':'cancelled'}}
        v=self.value(r);self.assertEqual((v['retained_lower_ns'],v['retained_upper_ns']),(0,60));self.assertEqual(v['measurement_class'],'INTERRUPTION_CENSORED')
    def test_false_normal_after_async_release_not_promoted(self):
        r=trace();r[-1]['status']='expired';r[-1]['interruption']={'intent_token':'t','record':{'verified':True,'keys_down':[],'buttons_down':[], 'verified_ns':70,'reason':'expired'}}
        self.assertEqual(self.value(r)['retained_lower_ns'],0)
    def test_repeated_key_after_release_is_allowed(self):
        r=trace();down=copy.deepcopy(r[1]);up=copy.deepcopy(r[2]);down.update(admitted_ns=91,input_ack_ns=92);up.update(release_call_started_ns=93,release_call_returned_ns=94);r[-1:-1]=[down,up]
        self.assertEqual(self.value(r)['admission_count'],2)
    def test_union_matches_discrete_oracle(self):
        rng=random.Random(88)
        for _ in range(5000):
            ins=[tuple(sorted((rng.randrange(100),rng.randrange(100)))) for j in range(rng.randrange(12))]
            a,b=sorted((rng.randrange(101),rng.randrange(101)))
            actual=sum(any(l<=x<r for l,r in ins) for x in range(a,b))
            self.assertEqual(union_ns(ins,a,b),actual)
    def test_bound_inclusion_property(self):
        rng=random.Random(89)
        for _ in range(5000):
            lower=[];true=[];upper=[]
            for i in range(rng.randrange(1,8)):
                a,b,c,d=sorted(rng.sample(range(100),4));x=rng.randint(a,b);y=rng.randint(c,d)
                lower.append((b,c));upper.append((a,d));true.append((x,y))
            l,t,u=(union_ns(x,15,85) for x in (lower,true,upper))
            self.assertLessEqual(l,t);self.assertLessEqual(t,u)

if __name__=='__main__':unittest.main()
