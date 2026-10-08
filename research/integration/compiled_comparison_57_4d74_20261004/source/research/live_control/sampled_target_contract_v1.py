"""Application-independent sampled patch contract. Returns evidence, never input authority."""
import hashlib


def evaluate(contract,intent,source,fresh,source_image,fresh_image,now_ns):
 def refuse(reason):return {'eligible':False,'reason':reason}
 try:
  if type(contract) is not dict or set(contract)!={'name','box','point','max_age_ms'}:return refuse('invalid_contract')
  if type(contract['name']) is not str or not contract['name'] or len(contract['name'])>128:return refuse('invalid_contract')
  box,point,age=contract['box'],contract['point'],contract['max_age_ms']
  if type(box) is not list or len(box)!=4 or any(type(n) is not int for n in box):return refuse('invalid_contract')
  if type(point) is not list or len(point)!=2 or any(type(n) is not int for n in point):return refuse('invalid_contract')
  if type(age) is not int or not 1<=age<=1000:return refuse('invalid_contract')
  if not 0<=box[0]<=point[0]<box[2] or not 0<=box[1]<=point[1]<box[3]:return refuse('invalid_contract')
  if type(intent) is not dict or set(intent)!={'intent','execute_once'} or type(intent['intent']) is not str or intent['intent']!=contract['name'] or intent['execute_once'] is not True:return refuse('invalid_intent')
  for obs in (source,fresh):
   if type(obs['sequence']) is not int or obs['sequence']<1 or type(obs['capture_ns']) is not int or obs['capture_ns']<0:return refuse('invalid_observation')
  if fresh['sequence']<=source['sequence'] or fresh['capture_ns']<source['capture_ns']:return refuse('not_new_observation')
  if type(now_ns) is not int or not 0<=now_ns-fresh['capture_ns']<age*1_000_000:return refuse('freshness')
  binding=source.get('pointer_binding')
  if type(binding) is not dict or set(binding)!={'focus','surface','geometry'}:return refuse('binding_unknown')
  if any(type(binding[k]) is not int or binding[k]<=1 for k in ('focus','surface')):return refuse('binding_unknown')
  geometry=binding['geometry']
  if type(geometry) is not list or len(geometry)!=4 or any(type(n) is not int for n in geometry) or min(geometry[2:])<=0:return refuse('binding_unknown')
  if fresh.get('pointer_binding')!=binding:return refuse('binding_changed')
  if not geometry[0]<=point[0]<geometry[0]+geometry[2] or not geometry[1]<=point[1]<geometry[1]+geometry[3]:return refuse('point_outside_surface')
  for obs in (source,fresh):
   if obs['input_focus_before']!=binding['focus'] or obs['input_focus_after']!=binding['focus']:return refuse('focus_samples_disagree')
  for field in ('input_state_before','input_state_after'):
   sample=fresh[field]
   if type(sample['owned_buttons']) is not list or type(sample['owned_keycodes']) is not list:return refuse('invalid_observation')
   if sample['owned_buttons'] or sample['owned_keycodes']:return refuse('owned_input_active')
  if source_image.mode!=fresh_image.mode or source_image.size!=fresh_image.size:return refuse('image_shape_changed')
  if box[2]>source_image.width or box[3]>source_image.height:return refuse('outside_image')
  pixels=source_image.crop(box).tobytes()
  if pixels!=fresh_image.crop(box).tobytes():return refuse('target_patch_changed')
  return {'eligible':True,'reason':'sampled_patch_and_binding_match','contract':contract['name'],'point':point.copy(),'expected_sequence':fresh['sequence'],'valid_until_ns':fresh['capture_ns']+age*1_000_000,'patch_sha256':hashlib.sha256(pixels).hexdigest(),'authority':'none; caller must submit once through existing owner admission','scope':'sampled pixels only; no semantic identity, hidden-state or atomic input proof'}
 except (KeyError,TypeError,ValueError,IndexError,OverflowError):return refuse('invalid_observation')
