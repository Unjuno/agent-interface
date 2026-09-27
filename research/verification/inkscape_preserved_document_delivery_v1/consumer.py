"""Read-only adapter for a deliberately restricted, axis-aligned SVG contract.

No action or repair is performed here. The legacy reducer is byte-identical.
The adapter's unsupported vocabulary stays UNKNOWN instead of assuming safety.
"""
from decimal import Decimal, InvalidOperation
import hashlib
import xml.etree.ElementTree as ET
from legacy_reducer import reduce_outcome

SVG='http://www.w3.org/2000/svg'
DRAW={'rect','path','circle','ellipse','line','polyline','polygon','text','image','use','g','foreignObject'}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def number(value: str) -> str:
    if type(value) is not str: raise ValueError('numeric string required')
    v=Decimal(value)
    if not v.is_finite(): raise ValueError('nonfinite coordinate')
    return str(v.normalize())

def snapshot(doc: bytes, query: bytes) -> dict:
    root=ET.fromstring(doc)
    if root.tag!=f'{{{SVG}}}svg': raise ValueError('not SVG')
    if any(root.get(k) is not None for k in ('style','transform','opacity','class')): raise ValueError('unsupported root styling')
    if any(n.tag in {f'{{{SVG}}}style', f'{{{SVG}}}script'} for n in root.iter()): raise ValueError('unsupported stylesheet/script')
    # Fixed 1:1 user-unit document; no physical monitor conversion is asserted.
    if [number(root.get(k,'')) for k in ('width','height')]!=['3.2E+2','1.8E+2'] or root.get('viewBox')!='0 0 320 180':
        raise ValueError('unsupported coordinate system')
    q={}
    for line in query.decode('utf-8').splitlines():
        fields=line.split(',')
        if len(fields)!=5 or fields[0] in q: raise ValueError('query cardinality')
        q[fields[0]]=[number(v) for v in fields[1:]]
    objects={}
    for node in root.iter():
        if not node.tag.startswith('{'+SVG+'}'): continue
        tag=node.tag.rsplit('}',1)[-1]
        if tag not in DRAW: continue
        if tag!='rect' or node not in list(root): raise ValueError('unsupported shape/nesting')
        ident=node.get('id')
        if not ident or ident in objects: raise ValueError('object identity')
        allowed={'id','x','y','width','height','fill','style'}
        if any(k not in allowed for k in node.attrib): raise ValueError('unsupported rect attribute')
        style={}
        for item in node.get('style','').split(';'):
            if item.strip():
                k,v=item.split(':',1);k=k.strip();v=v.strip()
                if k in style: raise ValueError('duplicate style')
                style[k]=v
        if set(style)-{'fill'}: raise ValueError('unsupported style')
        fill=style.get('fill',node.get('fill'))
        if fill not in {'#ff00aa','#0080ff','#ff0000'}: raise ValueError('unsupported fill')
        geom=[number(node.get(k,'')) for k in ('x','y','width','height')]
        if any(Decimal(v)<0 for v in geom[2:]): raise ValueError('negative size')
        if q.get(ident)!=geom: raise ValueError('query/document disagreement')
        objects[ident]={'box':geom,'fill':fill}
    # Root and metadata IDs have no bearing on the shape-inventory contract.
    if not objects: raise ValueError('no objects')
    return {'objects':objects,'coordinate_system':'svg_user_unit_1_to_1_css_px'}

def evaluate(before_doc: bytes, before_query: bytes, after_doc: bytes, after_query: bytes,
             contract: dict, receipt: dict, view: str='full') -> dict:
    unavailable={'primary':None,'preserved':None,'legacy_outcome':'UNKNOWN',
                 'outcome':'UNKNOWN','required_only':'UNKNOWN','authority':False}
    try:
        if type(receipt) is not dict or type(receipt.get('exit')) is not int or receipt['exit']!=0:
            raise ValueError('process receipt')
        if set(contract)!={'before_sha256','target_id','translation_x','expected_ids'}: raise ValueError('contract schema')
        if contract['before_sha256']!=sha(before_doc) or type(contract['translation_x']) is not int:
            raise ValueError('contract binding')
        if receipt.get('document_sha256')!=sha(after_doc): raise ValueError('document binding')
        before=snapshot(before_doc,before_query)['objects'];after=snapshot(after_doc,after_query)['objects']
        target=contract['target_id']
        if target not in before or sorted(before)!=contract['expected_ids']: raise ValueError('input scope')
        wanted=list(before[target]['box']);wanted[0]=number(str(Decimal(wanted[0])+contract['translation_x']))
        primary=target in after and after[target]['box']==wanted
        preserved=(set(before)==set(after) and target in after and after[target]['fill']==before[target]['fill']
                   and all(before[k]==after[k] for k in before if k!=target))
        if view=='collateral_withheld': preserved=None
        elif view!='full': raise ValueError('unsupported view')
        old=reduce_outcome(primary,preserved,True)
        return {'primary':primary,'preserved':preserved,'legacy_outcome':old,
                'outcome':{'PARTIAL_PRIMARY_RESTORED':'PARTIAL_REQUIRED_EFFECT_ONLY'}.get(old,old),
                'required_only':'COMPLETE_SUCCESS' if primary else 'FAILURE','authority':False}
    except (KeyError,ValueError,TypeError,InvalidOperation,ET.ParseError,UnicodeError):
        return unavailable
