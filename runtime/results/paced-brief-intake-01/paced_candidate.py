import copy,hashlib,json
from runtime.core_v1.sequence import expand_text_gaps
def encode(v):
 return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def paced_projection(view,source_projection):
 full=copy.deepcopy(view)
 # Reuse the archived success/failure gate unchanged.
 base=source_projection(view)
 if base.get('presentation',{}).get('returned')!='brief':return full
 try:
  raw=view['receipt']['source']['raw_report'];execution=raw['result']['execution']
  comp=raw['compilation']
  if comp['kind']!='bounded_text_gap':return full
  operations,mapping=expand_text_gaps(comp['source_program']['ops'])
  if encode(mapping)!=encode(comp['operation_sources']):return full
  if encode(execution['completed_ops'])!=encode(list(range(len(operations)))):return full
  waits=execution['waits']
  expected=[(i,o['timeout_ms']) for i,o in enumerate(operations) if o['op']=='wait_update']
  if len(waits)!=len(expected) or not waits:return full
  keys={'operation_index','requested_ms','started_ns','completed','kind','update_observed','ended_ns'}
  for w,(index,requested) in zip(waits,expected):
   if set(w)!=keys:return full
   if any(type(w[n]) is not int for n in ('operation_index','requested_ms','started_ns','ended_ns')):return full
   if w['operation_index']!=index or w['requested_ms']!=requested:return full
   if w['started_ns']<0 or w['ended_ns']<w['started_ns']:return full
   if w['completed'] is not True or w['kind']!='fixed_delay' or w['update_observed'] is not None:return full
  target=base['receipt']['source']['report_projection']
  def marker(value):
   return {'sha256':hashlib.sha256(encode(value)).hexdigest(),'bytes':len(encode(value)),'encoding':'canonical JSON, UTF-8, sorted keys, compact, ensure_ascii=true'}
  target['result']['execution'].pop('waits')
  target['result']['execution']['wait_summary']={
   'count':len(waits),'requested_ms_total':sum(w['requested_ms'] for w in waits),
   'recorded_elapsed_ns_total':sum(w['ended_ns']-w['started_ns'] for w in waits),
   'kind':'fixed_delay','update_observed':None,'all_completed':True,
   'omitted_records':marker(waits)}
  target['compilation'].pop('operation_sources')
  target['compilation']['operation_sources_omitted']={'count':len(mapping),**marker(mapping)}
  base['receipt']['schema']='agent-interface/receipt-view-paced-brief-candidate-v1'
  base['presentation']['scope']='Partial success-only projection: source programs, wait records and expansion map omitted. Not lossless or task success.'
  base['presentation']['omitted_paths'] += ['/receipt/source/raw_report/result/execution/waits','/receipt/source/raw_report/compilation/operation_sources']
  # This engineering candidate has no installed tool/API support.
  base['presentation']['candidate_only']=True
  if len(encode(base))>=len(encode(view)):return full
  return base
 except (KeyError,TypeError,ValueError,AttributeError):return full
