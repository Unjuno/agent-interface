"""Synthetic checker-construction data only; never native result evidence."""
import copy,hashlib,json,unittest
from audit import check,controls,typed_equal
def corpus():
    rows=[]
    fields=('cover','geometry','focus','pending','business')
    for field in fields:
        for mode in ('RECUR','CLEAR','WITHHELD','NEW_FAILURE'):
            for arm in ('NO_MEMORY','NOTE','TYPED','FRESH','TYPED_PLUS_FRESH'):
                bad=field if mode=='RECUR' else fields[(fields.index(field)+1)%5] if mode=='NEW_FAILURE' else None
                def event_list(cause):
                    # Literal native contract: Button1 4/5; F8 2/3. Not auditor helper.
                    mouse=11 if cause=='cover' else 10;keyboard=11 if cause=='focus' else 10
                    return ([] if cause=='geometry' else [{'type':4,'window':mouse,'detail':1},{'type':5,'window':mouse,'detail':1}])+[{'type':2,'window':keyboard,'detail':74},{'type':3,'window':keyboard,'detail':74}]
                decisions={'NO_MEMORY':('TRY','TRY','TRY','TRY'),'NOTE':('BLOCK','BLOCK','BLOCK','BLOCK'),
                           'TYPED':('BLOCK','TRY','UNKNOWN','TRY'),'FRESH':('BLOCK','TRY','UNKNOWN','BLOCK'),
                           'TYPED_PLUS_FRESH':('BLOCK','TRY','UNKNOWN','BLOCK')}
                decision=decisions[arm][('RECUR','CLEAR','WITHHELD','NEW_FAILURE').index(mode)]
                prior={'events':event_list(field),'committed':False,'saved_bytes':None}
                obs={k:k!=bad for k in fields};supplied=dict(obs)
                if mode=='WITHHELD':supplied[field]=None
                committed=decision=='TRY' and bad is None
                rows.append(dict(field=field,mode=mode,arm=arm,target=10,cover=11,keycode=74,
                                 prior_observed={k:k!=field for k in fields},prior=prior,
                                 memory=dict(target='10',attempted_action='click_then_F8',observed_preconditions={k:k!=field for k in fields},
                                             applicability_envelope={'field':field,'value':False},outcome='NOT_COMMITTED',evidence=hashlib.sha256(json.dumps(prior,sort_keys=True).encode()).hexdigest()),
                                 current_observed=obs,supplied_observed={field:supplied[field]} if arm=='TYPED' else supplied,
                                 decision=decision,attempt=dict(events=event_list(bad) if decision=='TRY' else [],committed=committed,saved_bytes='434f4d4d49545445440a' if committed else None),
                                 keymap_empty=True,buttons_neutral=True,server_exit=0,cleanup_errors=[],memory_unchanged=True))
    return rows
class AuditTests(unittest.TestCase):
    def test_synthetic_checker_contract(self):self.assertEqual(check(corpus())['rows'],100)
    def test_copied_controls_effective_and_rejected(self):self.assertEqual(controls(corpus()),9)
    def test_bool_is_not_event_integer(self):
        rows=corpus();rows[0]['prior']['events'][0]['detail']=True
        with self.assertRaises(ValueError):check(rows)
    def test_different_failure_committed_is_refused(self):
        rows=corpus();rows[17]['attempt']['committed']=True
        with self.assertRaises(ValueError):check(rows)
    def test_missing_tail_refused(self):
        with self.assertRaises(ValueError):check(corpus()[:-1])
    def test_nested_type_equality(self):self.assertFalse(typed_equal({'a':[True]},{'a':[1]}))
if __name__=='__main__':unittest.main()
