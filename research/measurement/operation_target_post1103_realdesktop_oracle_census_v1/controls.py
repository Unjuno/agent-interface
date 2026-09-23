import copy,json
from pathlib import Path
from audit import verify
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/'RESULT.json').read_text());L=json.loads((HERE/'ledger.json').read_text());S=json.loads((HERE/'sources.json').read_text())
controls=[]
def t(name,mut_r=None,mut_l=None,mut_s=None):
 r=copy.deepcopy(R);l=copy.deepcopy(L);s=copy.deepcopy(S)
 if mut_r:mut_r(r)
 if mut_l:mut_l(l)
 if mut_s:mut_s(s)
 o=verify(r,l,s);controls.append({'name':name,'rejected':not o['audit_pass'],'errors':o['errors']})
t('inflate_qualified_positive',mut_r=lambda r:r.__setitem__('oracle_qualified_positive_rows',32))
t('launder_chromium_final_score',mut_l=lambda l:l['entries'][0]['gates'].__setitem__('finite_candidate_set',True))
t('launder_mindustry_currentness',mut_l=lambda l:l['entries'][3]['gates'].__setitem__('operation_target_choice_not_preselected',True))
t('launder_compiled_method',mut_l=lambda l:l['entries'][4]['gates'].__setitem__('independent_acceptable_set',True))
t('coerce_no_authority_to_direct_yield',mut_l=lambda l:l['entries'][2].__setitem__('direct_1015_compatible',True))
t('change_source_blob',mut_s=lambda s:s['blobs'].__setitem__('openttd_audit','0'*40))
assert all(x['rejected'] for x in controls),controls
(HERE/'CORRUPTION.json').write_text(json.dumps({'controls':controls,'rejected':sum(x['rejected'] for x in controls),'total':len(controls)},indent=2,sort_keys=True)+'\n')
print(json.dumps(controls,indent=2,sort_keys=True))
