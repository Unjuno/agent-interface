"""Read-only Chromium observation guards; proposals are NOT input authority.

A browser backend node is document-scoped identity, not business-object identity.
This prototype cannot make CDP reads and later XTest input atomic.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import time


@dataclass(frozen=True)
class Binding:
    document: int
    scope: int
    node: int
    role: str = 'button'
    name: str = 'Target'


def disabled(node):
    return any(p.get('name') == 'disabled' and
               p.get('value', {}).get('value') is True
               for p in node.get('properties', []))


def value(node, field):
    return node.get(field, {}).get('value')


def descendants(tree, root):
    index = {n['nodeId']: n for n in tree['nodes']}
    todo = [root['nodeId']]
    seen = set()
    while todo:
        k = todo.pop()
        if k in seen:
            continue
        seen.add(k)
        todo.extend(index.get(k, {}).get('childIds', []))
    return [n for n in tree['nodes'] if n['nodeId'] in seen]


def select(tree, document, binding=None):
    """Pure selector returns reason and selected node; no click and no scorer."""
    live = [n for n in tree['nodes'] if not n.get('ignored')]
    scopes = [n for n in live if value(n, 'role') == 'region'
              and value(n, 'name') == 'Workspace']
    if len(scopes) != 1:
        return 'SCOPE_CARDINALITY', None
    scope = scopes[0]
    if binding and (document != binding.document or
                    scope.get('backendDOMNodeId') != binding.scope):
        return 'BINDING_CHANGED', None
    nodes = [n for n in descendants(tree, scope)
             if not n.get('ignored') and value(n, 'role') == 'button'
             and value(n, 'name') == 'Target']
    if len(nodes) != 1:
        return 'TARGET_CARDINALITY', None
    node = nodes[0]
    if binding and node.get('backendDOMNodeId') != binding.node:
        return 'TARGET_REPLACED', None
    if disabled(node):
        return 'DISABLED', None
    return 'SELECTED', node


def observe(cdp):
    start = time.perf_counter_ns()
    doc = cdp.send('DOM.getDocument', {'depth': 0})['root']['backendNodeId']
    tree = cdp.send('Accessibility.getFullAXTree')
    return {'document': doc, 'tree': tree, 'start_ns': start,
            'end_ns': time.perf_counter_ns()}


def acquire(cdp):
    obs = observe(cdp)
    reason, node = select(obs['tree'], obs['document'])
    if node is None:
        raise RuntimeError('source acquisition failed: ' + reason)
    scopes = [n for n in obs['tree']['nodes'] if not n.get('ignored')
              and value(n, 'role') == 'region' and value(n, 'name') == 'Workspace']
    b = Binding(obs['document'], scopes[0]['backendDOMNodeId'], node['backendDOMNodeId'])
    return b, obs


def propose(cdp, binding=None):
    obs = observe(cdp)
    reason, node = select(obs['tree'], obs['document'], binding)
    obs.update(reason=reason, point=None, binding=asdict(binding) if binding else None)
    if node is None:
        return obs
    try:
        box = cdp.send('DOM.getBoxModel', {'backendNodeId': node['backendDOMNodeId']})
        pts = box['model']['border']
        x, y = sum(pts[::2]) / 4, sum(pts[1::2]) / 4
        if not all(math.isfinite(a) for a in (x, y)) or not (0 <= x < 800 and 0 <= y < 600):
            obs['reason'] = 'OFF_SURFACE'
            return obs
        point = [round(x), round(y)]
        hit = cdp.send('DOM.getNodeForLocation', {'x': point[0], 'y': point[1],
                       'includeUserAgentShadowDOM': True, 'ignorePointerEventsNone': False})
        obs.update(box=box, hit=hit)
        if hit.get('backendNodeId') != node['backendDOMNodeId']:
            obs['reason'] = 'OCCLUDED'
        else:
            obs.update(reason='PROPOSED', point=point)
    except Exception as exc:
        obs.update(reason='OBSERVATION_ERROR', error=str(exc))
    finally:
        obs['end_ns'] = time.perf_counter_ns()
    return obs
