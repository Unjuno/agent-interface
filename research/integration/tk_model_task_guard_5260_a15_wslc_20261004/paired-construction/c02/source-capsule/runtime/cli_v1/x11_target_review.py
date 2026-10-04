"""Read-only focused-client evidence for explicit persistent X11 target review.

WM properties are application metadata, not authenticated identity. This does not
prove visual freshness or authorize input; ordinary dispatch admission remains.
"""
def read_window_title(connection, window):
    """Prefer public UTF-8 title properties, as on the guarded X11 route."""
    for name in ('_NET_WM_NAME', '_NET_WM_VISIBLE_NAME'):
        prop = window.get_full_property(connection.intern_atom(name),
                                        connection.intern_atom('UTF8_STRING'))
        if prop is not None:
            if prop.format != 8:
                raise ValueError('invalid UTF-8 window title format')
            title = bytes(prop.value).decode('utf-8', errors='strict')
            if title:
                return title
    title = window.get_wm_name()
    return title.decode('utf-8', 'replace') if isinstance(title, bytes) else title


def inspect_focused_target(backend, family_root):
    from Xlib import X
    d, root = backend.d, backend.root
    prop = root.get_full_property(d.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
    if prop is None or prop.format != 32 or len(prop.value) > 4096:
        raise ValueError('managed client inventory unavailable or too large')
    managed = {int(x) for x in prop.value}
    # Configured input targets can be toolkit children (for example Tk's
    # winfo_id). Resolve their actual managed ancestor without changing the
    # binding. Keep the ancestry in review evidence so reparenting invalidates
    # the existing one-use review rather than silently choosing a new family.
    family_path = [family_root]
    family_client = family_root
    if family_root not in managed:
        configured = d.create_resource_object('window', family_root)
        for _ in range(63):
            configured = configured.query_tree().parent
            wid = getattr(configured, 'id', None)
            if not wid or wid in family_path or wid == root.id:
                raise ValueError('configured managed client unavailable')
            family_path.append(wid)
            if wid in managed:
                family_client = wid
                break
        else:
            raise ValueError('configured target ancestry exceeds limit')
    focus = d.get_input_focus().focus
    focus_path = []
    for _ in range(64):
        wid = getattr(focus, 'id', None)
        if not wid or wid in focus_path:
            raise ValueError('focused managed client unavailable')
        focus_path.append(wid)
        if wid in managed:
            break
        focus = focus.query_tree().parent
    else:
        raise ValueError('focus ancestry exceeds limit')
    win = focus
    if win.get_attributes().map_state != X.IsViewable:
        raise ValueError('focused client is not viewable')
    chain = [win.id]
    current = win
    for _ in range(16):
        if current.id == family_client:
            break
        current = current.get_wm_transient_for()
        if current is None or current.id in chain:
            raise ValueError('focused client is outside configured transient family')
        chain.append(current.id)
    else:
        raise ValueError('transient ancestry exceeds limit')
    geo = win.get_geometry()
    point = root.translate_coords(win, 0, 0)
    title = read_window_title(d, win)
    evidence = {'window_id': win.id, 'focus_path': focus_path,
            'transient_chain': chain, 'family_root': family_root,
            'title': title, 'wm_class': list(win.get_wm_class() or ()),
            'geometry': [point.x, point.y, geo.width, geo.height]}

    if len(family_path) > 1:
        evidence.update(configured_target_path=family_path, managed_family_root=family_client)
    return evidence
