"""Independent task oracles; never imported by the pixel controller."""
from pathlib import Path
import xml.etree.ElementTree as ET
import math
NS='{http://www.w3.org/2000/svg}'

def svg_snapshot(path):
    root=ET.fromstring(Path(path).read_bytes());items={}
    for el in root.iter():
        if not el.tag.startswith(NS):continue
        tag=el.tag[len(NS):]
        if tag in ('svg','defs','metadata'):continue
        ident=el.get('id')
        if not ident:raise ValueError('renderable SVG element missing stable ID')
        items[ident]=(el.tag,{k:v for k,v in el.attrib.items() if not k.startswith('{')},(el.text or '').strip())
    # Numeric canvas and root style must remain unchanged; auto-assigned ID ignored.
    root_attrs={k:v for k,v in root.attrib.items() if not k.startswith('{') and k not in ('id','version')}
    return items,root_attrs

def svg_outcome(before,after,removed_before=False):
    if removed_before:
        same=Path(before).read_bytes()==Path(after).read_bytes()
        return dict(independent_success=same,oracle='exact_no_further_change_after_target_removed',exact_bytes_unchanged=same)
    a,ar=svg_snapshot(before);b,br=svg_snapshot(after)
    lost=sorted(set(a)-set(b));added=sorted(set(b)-set(a));changed=sorted(k for k in set(a)&set(b) if a[k]!=b[k])
    return dict(independent_success=lost==['task-target'] and not added and not changed and ar==br,oracle='persisted_svg_delete_only_target',oracle_removed=lost,oracle_added=added,oracle_changed=changed,canvas_unchanged=ar==br)

def doom_outcome(score):
    # Frozen setup-derived destination beyond the first door, not a controller waypoint.
    valid=all(math.isfinite(float(score[k])) for k in ('forward_displacement','cross_track_displacement'))
    success=valid and score['forward_displacement']>=1100 and abs(score['cross_track_displacement'])<=96 and score['final']['POSITION_Z']<=-120 and not score['dead'] and not score['timeout']
    return dict(independent_success=bool(success),oracle='initial_door_transit_destination',full_map_clear=False)
