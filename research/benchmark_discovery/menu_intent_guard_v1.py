"""Single known-menu intent guard; no execution, lease renewal or retry."""

def check(intent,source,fresh,source_image,fresh_image,now_ns):
 if intent!={'intent':'select_basic_conveyor','execute_once':True}:return {'eligible':False,'reason':'unsupported_intent'}
 if type(now_ns) is not int or not 0<=now_ns-fresh['capture_ns']<1_000_000_000:return {'eligible':False,'reason':'freshness'}
 if fresh['sequence']<=source['sequence']:return {'eligible':False,'reason':'not_new_observation'}
 binding=source.get('pointer_binding')
 if not binding or not binding.get('surface') or fresh.get('pointer_binding')!=binding:return {'eligible':False,'reason':'binding_changed'}
 state=fresh['input_state_after']
 if state['owned_buttons'] or state['owned_keycodes']:return {'eligible':False,'reason':'owned_input_active'}
 if source_image.size!=fresh_image.size:return {'eligible':False,'reason':'image_size_changed'}
 box=(985,551,1032,603)
 if source_image.width<box[2] or source_image.height<box[3]:return {'eligible':False,'reason':'outside_image'}
 if source_image.crop(box).tobytes()!=fresh_image.crop(box).tobytes():return {'eligible':False,'reason':'target_patch_changed'}
 return {'eligible':True,'reason':'known_menu_patch_and_binding_match','box':list(box),'point':[1008,578],'valid_until_ns':fresh['capture_ns']+1_000_000_000,'scope':'local sampled patch, not semantic identity or atomic capture/input proof'}
