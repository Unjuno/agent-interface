FIELDS=('window_id','x','y','width','height','map_state')
def authorize(cached,candidates):
 if candidates is None:return 'UNAVAILABLE'
 if len(candidates)==0:return 'NO_MATCH'
 if len(candidates)!=1:return 'AMBIGUOUS'
 current=candidates[0]
 if any(type(g) is not dict or any(type(g.get(k)) is not int for k in FIELDS) for g in (cached,current)):return 'UNAVAILABLE'
 if current['map_state']!=2 or current['width']<=0 or current['height']<=0:return 'UNAVAILABLE'
 return 'ACCEPT' if all(cached[k]==current[k] for k in FIELDS) else 'STALE_GEOMETRY'
