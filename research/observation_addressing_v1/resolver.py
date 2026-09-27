"""Calibrated addressing mechanics, not a learned grounding model or authority."""
import cv2
import numpy as np

ARMS = ('coordinate', 'grid_center', 'grid_candidates', 'predict', 'ax', 'hybrid')

def regions(rgb):
    mask = np.all(np.asarray(rgb) == (220, 40, 180), axis=2).astype('uint8')
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    return [list(map(int, s[:4])) for s in stats[1:count] if s[4] >= 12]

def center(box):
    x, y, w, h = box
    return [x + w / 2, y + h / 2]

def contains(box, point):
    x, y, w, h = box
    return x <= point[0] < x+w and y <= point[1] < y+h

def cell(point, size=128):
    return [int(point[0]//size), int(point[1]//size)]

def resolve(arm, previous, source, current, native, size=128):
    """Inputs are observed regions and public AX/DOM boxes; never fixture truth."""
    if arm not in ARMS:
        raise ValueError('unknown arm')
    if len(previous) != 1 or len(source) != 1:
        return {'status':'SOURCE_AMBIGUOUS','point':None}
    a, b = center(previous[0]), center(source[0])
    point, status = None, 'AMBIGUOUS_OR_MISSING'
    if arm == 'coordinate': point, status = b, 'SOURCE_COORDINATE'
    elif arm == 'grid_center':
        c=cell(b,size);point=[(c[0]+.5)*size,(c[1]+.5)*size];status='CELL_CENTER'
    elif arm == 'predict':
        point=[2*b[0]-a[0],2*b[1]-a[1]];status='DISCRETE_EXTRAPOLATION'
    elif arm == 'grid_candidates':
        candidates=[x for x in current if cell(center(x),size)==cell(b,size)]
        if len(candidates)==1: point, status=center(candidates[0]), 'CELL_UNIQUE_CURRENT'
    elif arm == 'ax':
        targets=[x['box'] for x in native if x['name']=='Save']
        if len(targets)==1: point, status=center(targets[0]),'NATIVE_UNIQUE_CURRENT'
    else:
        targets=[x['box'] for x in native if x['name']=='Save']
        matches=[x for x in current if any(contains(y,center(x)) for y in targets)]
        if len(matches)==1: point,status=center(matches[0]),'CROSS_MODAL_AGREEMENT'
        elif not targets and len(current)==1 and not native:
            point,status=center(current[0]),'PIXEL_FALLBACK_NATIVE_ABSENT'
        elif current and native and not matches: status='CROSS_MODAL_CONFLICT'
    if point is not None and not (0<=point[0]<800 and 0<=point[1]<600):
        point,status=None,'OUT_OF_BOUNDS'
    return {'status':status,'point':point}
