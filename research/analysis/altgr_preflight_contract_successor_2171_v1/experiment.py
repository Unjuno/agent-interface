import json
STATES=['DIRECT_LEVEL0_3','DEAD_OR_COMPOSE_REQUIRED','MAP_STALE_OR_CHANGED','MODIFIER_STATE_UNKNOWN','ALTERNATE_TEXT_PATH','PARTIAL_DELIVERY_OR_UNKNOWN_EFFECT']
def decision(s): return 'DIRECT_TYPE' if s=='DIRECT_LEVEL0_3' else ('ALTERNATE_PATH' if s=='ALTERNATE_TEXT_PATH' else 'ABORT')
def main():
 rows=[{'state':s,'decision':decision(s),'direct_key_emission':s=='DIRECT_LEVEL0_3','fail_closed':s!='DIRECT_LEVEL0_3'} for s in STATES]
 with open('RESULT.json','w',encoding='utf-8') as f: json.dump({'rows_detail':rows},f,sort_keys=True,indent=2)
 print('rows=6 direct_type=1 unsafe_direct=0')
if __name__=='__main__': main()
