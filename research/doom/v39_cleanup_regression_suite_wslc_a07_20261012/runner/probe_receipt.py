import json,sys
from pathlib import Path
root=Path('/mnt/d/codex-research/scratch/v39_cleanup_regression_suite_wslc_a07_20261012/inputs')
sys.path[:0]=[str(root/'main'),str(root/'candidate')]
from test_controller_failure_cleanup_v39 import ControllerFailureCleanupReleaseIdentityTests as T
cases={
'duplicate_acceptance':[{'event':'accepted','id':'source-refresh-0','intent_token':'accepted-lease-a'},{'event':'accepted','id':'source-refresh-0','intent_token':'accepted-lease-b'},{'event':'terminal','id':'source-refresh-0','release':{'verified':True,'keys_down':[],'buttons_down':[],'intent_token':'accepted-lease-b'}}],
'duplicate_terminals_forward':[{'event':'accepted','id':'source-refresh-0','intent_token':'accepted-lease'},{'event':'terminal','id':'source-refresh-0','release':{'verified':True,'keys_down':[],'buttons_down':[],'intent_token':'accepted-lease'}},{'event':'terminal','id':'source-refresh-0','release':{'verified':False,'keys_down':[38],'buttons_down':[]}}],
'duplicate_terminals_reverse':[{'event':'accepted','id':'source-refresh-0','intent_token':'accepted-lease'},{'event':'terminal','id':'source-refresh-0','release':{'verified':False,'keys_down':[38],'buttons_down':[]}},{'event':'terminal','id':'source-refresh-0','release':{'verified':True,'keys_down':[],'buttons_down':[],'intent_token':'accepted-lease'}}],
}
for name,rows in cases.items():
    rec=T().run_cleanup(events=rows)
    print(json.dumps({'case':name,'input_terminals_complete':rec.get('input_terminals_complete'),'input_releases_verified_empty':rec.get('input_releases_verified_empty'),'input_release_verified_empty':rec.get('input_release_verified_empty'),'reader_retired':rec.get('stdout_reader_retired'),'reader_errors':rec.get('stdout_reader_errors'),'stages':rec.get('stages')},sort_keys=True))
