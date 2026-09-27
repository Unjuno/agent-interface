import argparse,json
ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--journal',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
m=json.load(open(a.manifest,encoding='utf-8'))
events=[json.loads(x) for x in open(a.journal,encoding='utf-8') if x.strip()]
matched=[e for e in events if e.get('kind')=='task_effect' and e.get('scored') is True and e.get('plan_id')==m['plan_id'] and e.get('actuation_id')==m['actuation_id'] and e.get('source') in ('key_press','key_release')]
if len(matched)==1:
 r={'disposition':'TASK_EFFECT','plan_id':m['plan_id'],'actuation_id':m['actuation_id'],'t_ns':matched[0]['t_ns'],'source':matched[0]['source'],'scored':True,'authority':'none','scorer':'raw-app-journal-v1'}
else:
 r={'disposition':'UNRESOLVED_NO_TASK_EFFECT','plan_id':m['plan_id'],'actuation_id':m['actuation_id'],'t_ns':None,'source':None,'scored':False,'authority':'none','scorer':'raw-app-journal-v1'}
json.dump(r,open(a.out,'w',encoding='utf-8'),sort_keys=True,indent=2)
