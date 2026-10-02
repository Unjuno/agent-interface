import copy
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import candidate
import auditor

def main():
    fixture=json.loads((HERE/'input/cases.json').read_text())['cases']
    oracle=json.loads((HERE/'oracle.json').read_text())['expected_outcomes']
    rows=candidate.run(HERE/'input/cases.json')
    baseline=auditor.audit_rows(fixture,rows,oracle)
    assert baseline['decision']=='PASS_METHOD_SCOPED' and baseline['rows']==32
    mutants=[]
    def alter(name,case_id,policy,fn):
        changed=copy.deepcopy(rows)
        row=next(r for r in changed if r['case']==case_id and r['policy']==policy)
        fn(row)
        mutants.append((name,auditor.audit_rows(fixture,changed,oracle)['decision']))
    alter('drop_generic_answer','eligible_hidden_forbidden','GENERIC',lambda r:r.update(new_clauses=[],outcome='UNKNOWN',contract_revision_after=r['contract_revision_before']))
    alter('promote_unauthorized','unauthorized_respondent','GENERIC',lambda r:r.update(new_clauses=[{'effect':'send','stance':'ALLOW','scope':'all','provenance':[]}],outcome='APPENDED_ALLOW_SCOPED',contract_revision_after=r['contract_revision_before']+1))
    alter('admit_stale','stale_answer_after_revision','GENERIC',lambda r:r.update(outcome='APPENDED_ALLOW_SCOPED'))
    alter('leak_private','privacy_blocked_question','GENERIC',lambda r:r.update(private_data_displayed=True))
    alter('no_answer_to_allow','unknown_decline_noanswer','GENERIC',lambda r:r.update(outcome='APPENDED_ALLOW_SCOPED'))
    alter('rewrite_source_clause','source_stated_prohibition','SOURCE_ONLY',lambda r:r['source_clauses'][0].update(stance='ALLOW'))
    alter('mint_dispatch_authority','eligible_scoped_allow','GENERIC',lambda r:r.update(authority_granted=True))
    assert all(decision=='FAIL_METHOD' for _,decision in mutants),mutants
    print(json.dumps({'construction':'PASS','rows':32,'mutations':dict(mutants)},sort_keys=True))

if __name__=='__main__': main()
