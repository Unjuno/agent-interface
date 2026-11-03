"""Exact Linux process-group custody for bounded Calc orphan cleanup.

This module never treats a numeric PGID as sufficient authority. A caller must
retain the launcher's PID/start tick and the bound Calc GUI PID/start tick, and
the observed group may contain only those exact process generations.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import time


_CUSTODY_SCHEMA = 'agent-interface/calc-process-group-custody-v1'
_CLEANUP_SCHEMA = 'agent-interface/calc-process-group-cleanup-v1'
_SIGTERM = getattr(signal, 'SIGTERM', 15)
_SIGKILL = getattr(signal, 'SIGKILL', 9)


def _signal_label(value):
    if value == _SIGTERM:
        return 'SIGTERM'
    if value == _SIGKILL:
        return 'SIGKILL'
    return str(value)


def _unsupported_killpg(_pgid, _signal):
    raise OSError('process-group signaling is unavailable on this platform')


def _parse_proc_stat(pid, raw):
    """Parse identity fields despite spaces and ')' characters in comm."""
    if type(pid) is not int or pid <= 0 or type(raw) is not str:
        raise ValueError('invalid proc stat input')
    opening, closing = raw.find('('), raw.rfind(')')
    if opening < 1 or closing <= opening or raw[:opening].strip() != str(pid):
        raise ValueError('proc stat PID or comm framing mismatch')
    fields = raw[closing + 1:].split()
    if len(fields) <= 19:
        raise ValueError('proc stat is truncated')
    state = fields[0]
    values = fields[1:]
    if (len(values) <= 18 or not values[0].isascii() or not values[0].isdigit()
            or not values[1].isascii() or not values[1].isdigit()
            or not values[2].isascii() or not values[2].isdigit()
            or len(values) <= 18 or not values[18].isascii()
            or not values[18].isdigit()):
        raise ValueError('proc stat identity fields are malformed')
    # values[0:3] are ppid, pgrp, session; values[18] is field 22 starttime.
    start_ticks = values[18]
    if not start_ticks.isascii() or not start_ticks.isdigit():
        raise ValueError('proc stat start tick is malformed')
    return {'pid':pid, 'state':state, 'parent_pid':int(values[0]),
        'process_group':int(values[1]), 'session_id':int(values[2]),
        'start_ticks':int(start_ticks)}


def read_linux_process_group(pgid, session_id, *, proc_root='/proc'):
    """Read every visible process in one exact group; fail on unreadable rows."""
    if (type(pgid) is not int or pgid <= 0 or type(session_id) is not int
            or session_id <= 0):
        raise ValueError('positive PGID and session ID required')
    root = Path(proc_root)
    result = []
    for entry in root.iterdir():
        if not entry.name.isascii() or not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            raw = (entry / 'stat').read_text(encoding='ascii')
        except FileNotFoundError:
            # The process exited between procfs enumeration and the read.
            continue
        row = _parse_proc_stat(pid, raw)
        if row['process_group'] == pgid and row['session_id'] == session_id:
            result.append(row)
    return sorted(result, key=lambda row: row['pid'])


def read_linux_process_generation(pid, *, proc_root='/proc'):
    """Return one PID's current kernel generation, or None if it is absent."""
    if type(pid) is not int or pid <= 0:
        raise ValueError('positive process PID required')
    path = Path(proc_root) / str(pid) / 'stat'
    try:
        raw = path.read_text(encoding='ascii')
    except FileNotFoundError:
        return None
    return _parse_proc_stat(pid, raw)


def make_process_group_custody(*, leader_pid, leader_start_ticks,
        target_pid, target_start_ticks, group_snapshot):
    """Validate the fresh group and create a small parent-retained receipt."""
    values = (leader_pid, leader_start_ticks, target_pid, target_start_ticks)
    if any(type(value) is not int or value <= 0 for value in values):
        raise ValueError('exact positive launcher and target identities required')
    if leader_pid == target_pid or not isinstance(group_snapshot, (list, tuple)):
        raise ValueError('distinct process generations and a group snapshot required')
    expected = {leader_pid:leader_start_ticks, target_pid:target_start_ticks}
    observed = {}
    for row in group_snapshot:
        if not isinstance(row, dict):
            raise ValueError('malformed process group member')
        pid, ticks = row.get('pid'), row.get('start_ticks')
        pgid, sid = row.get('process_group'), row.get('session_id')
        if (type(pid) is not int or type(ticks) is not int or ticks <= 0
                or pgid != leader_pid or sid != leader_pid
                or pid not in expected or expected[pid] != ticks
                or pid in observed):
            raise ValueError('process group contains an unowned or changed member')
        observed[pid] = ticks
    if observed != expected:
        raise ValueError('launcher and bound GUI must both be live in the dedicated group')
    return {'schema':_CUSTODY_SCHEMA, 'pgid':leader_pid,
        'session_id':leader_pid,
        'launcher':{'pid':leader_pid,'start_ticks':leader_start_ticks},
        'target':{'pid':target_pid,'start_ticks':target_start_ticks},
        'expected_members':{str(pid):ticks for pid,ticks in sorted(expected.items())}}


def make_launcher_process_group_custody(*, leader_pid, leader_start_ticks,
        group_snapshot):
    """Retain a just-started dedicated launcher before its GUI child exists."""
    if (type(leader_pid) is not int or leader_pid <= 0
            or type(leader_start_ticks) is not int or leader_start_ticks <= 0
            or not isinstance(group_snapshot, (list, tuple))):
        raise ValueError('exact launcher identity and process-group snapshot required')
    observed={}
    for row in group_snapshot:
        if not isinstance(row,dict):
            raise ValueError('malformed process group member')
        pid,ticks=row.get('pid'),row.get('start_ticks')
        if (type(pid) is not int or type(ticks) is not int or ticks <= 0
                or row.get('process_group')!=leader_pid
                or row.get('session_id')!=leader_pid or pid!=leader_pid
                or ticks!=leader_start_ticks or pid in observed):
            raise ValueError('launcher-only group contains an unowned member')
        observed[pid]=ticks
    if observed!={leader_pid:leader_start_ticks}:
        raise ValueError('launcher-only group must contain the exact launcher')
    return {'schema':_CUSTODY_SCHEMA,'pgid':leader_pid,
        'session_id':leader_pid,
        'launcher':{'pid':leader_pid,'start_ticks':leader_start_ticks},
        'target':None,
        'expected_members':{str(leader_pid):leader_start_ticks}}


def advance_process_group_custody(previous, *, target_pid, target_start_ticks,
        group_snapshot, process_generation_reader=read_linux_process_generation):
    """Advance pre-review cleanup custody to one exact replacement GUI child.

    The launcher generation must remain identical, the previous GUI generation
    must be absent system-wide, and the fresh group snapshot must contain only
    the launcher plus the new direct child. This is cleanup custody only; it
    does not prove a clean application exit, input release, or task effect.
    """
    if not isinstance(previous, dict) or previous.get('schema') != _CUSTODY_SCHEMA:
        raise ValueError('previous process-group custody required')
    launcher = previous.get('launcher')
    old_target = previous.get('target')
    if (not isinstance(launcher, dict)
            or type(launcher.get('pid')) is not int
            or type(launcher.get('start_ticks')) is not int
            or previous.get('pgid') != launcher.get('pid')
            or previous.get('session_id') != launcher.get('pid')):
        raise ValueError('previous custody identity malformed')
    expected_previous={str(launcher['pid']):launcher['start_ticks']}
    if isinstance(old_target,dict):
        if (type(old_target.get('pid')) is not int
                or type(old_target.get('start_ticks')) is not int):
            raise ValueError('previous target identity malformed')
        expected_previous[str(old_target['pid'])]=old_target['start_ticks']
    elif old_target is not None:
        raise ValueError('previous target identity malformed')
    if previous.get('expected_members')!=expected_previous:
        raise ValueError('previous custody membership malformed')
    if (type(target_pid) is not int or target_pid <= 0
            or (old_target is not None and target_pid == old_target['pid'])
            or type(target_start_ticks) is not int or target_start_ticks <= 0
            or not callable(process_generation_reader)):
        raise ValueError('distinct exact replacement process generation required')
    if old_target is not None:
        old_live = process_generation_reader(old_target['pid'])
        if (old_live is not None
                and old_live.get('start_ticks') == old_target['start_ticks']):
            raise ValueError('previous GUI process generation is still live')
    rows = list(group_snapshot) if isinstance(group_snapshot, (list, tuple)) else None
    if rows is None:
        raise ValueError('replacement process-group snapshot required')
    target_rows = [row for row in rows
        if isinstance(row, dict) and row.get('pid') == target_pid]
    if (len(target_rows) != 1
            or target_rows[0].get('start_ticks') != target_start_ticks
            or target_rows[0].get('parent_pid') != launcher['pid']):
        raise ValueError('replacement GUI must be the exact direct child generation')
    return make_process_group_custody(
        leader_pid=launcher['pid'],leader_start_ticks=launcher['start_ticks'],
        target_pid=target_pid,target_start_ticks=target_start_ticks,
        group_snapshot=rows)


def cleanup_process_group(custody, *, group_snapshot_reader=read_linux_process_group,
        killpg=None, monotonic=time.monotonic, sleep=time.sleep,
        term_grace_s=0.5, kill_settle_s=0.5):
    """Boundedly terminate only the exact retained group; never certify clean exit."""
    def unknown(reason, *, signals=(), members=None):
        return {'schema':_CLEANUP_SCHEMA,'status':'unknown','reason':reason,
            'verified_empty':False,'clean_exit_verified':False,
            'signals_sent':list(signals),'members':members,
            'task_success':None,'replay_allowed':False}

    if not isinstance(custody, dict) or custody.get('schema') != _CUSTODY_SCHEMA:
        return unknown('custody_schema_invalid')
    if killpg is None:
        killpg = getattr(os, 'killpg', _unsupported_killpg)
    pgid, sid = custody.get('pgid'), custody.get('session_id')
    leader, target = custody.get('launcher'), custody.get('target')
    expected = custody.get('expected_members')
    if (type(pgid) is not int or pgid <= 0 or sid != pgid
            or not isinstance(leader, dict) or (target is not None and not isinstance(target,dict))
            or type(leader.get('pid')) is not int
            or leader.get('pid') != pgid
            or type(leader.get('start_ticks')) is not int
            or leader.get('start_ticks') <= 0
            or expected != ({str(leader['pid']):leader['start_ticks']} if target is None else
                {str(leader['pid']):leader['start_ticks'],
                 str(target.get('pid')):target.get('start_ticks')})
            or (target is not None and
                (type(target.get('pid')) is not int or target.get('pid') == pgid
                 or type(target.get('start_ticks')) is not int
                 or target.get('start_ticks') <= 0))):
        return unknown('custody_identity_invalid')
    if (type(term_grace_s) not in (int, float) or not 0 <= term_grace_s <= 5
            or type(kill_settle_s) not in (int, float)
            or not 0 <= kill_settle_s <= 5):
        return unknown('cleanup_deadline_invalid')

    allowed = {leader['pid']:leader['start_ticks']}
    if target is not None:
        allowed[target['pid']]=target['start_ticks']

    def snapshot():
        rows = group_snapshot_reader(pgid, sid)
        if not isinstance(rows, (list, tuple)):
            raise ValueError('process group snapshot is malformed')
        seen = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError('process group member is malformed')
            pid, ticks = row.get('pid'), row.get('start_ticks')
            if (type(pid) is not int or type(ticks) is not int or ticks <= 0
                    or row.get('process_group') != pgid
                    or row.get('session_id') != sid
                    or pid not in allowed or allowed[pid] != ticks
                    or pid in seen):
                raise ValueError('process group has unknown or reused member')
            seen[pid] = ticks
        return sorted(seen)

    try:
        members = snapshot()
    except Exception:
        return unknown('process_group_identity_unavailable')
    if not members:
        return {'schema':_CLEANUP_SCHEMA,'status':'already_empty',
            'verified_empty':True,'clean_exit_verified':False,'signals_sent':[],
            'members':[],'task_success':None,'replay_allowed':False}

    signals = []
    try:
        killpg(pgid, _SIGTERM)
        signals.append(_signal_label(_SIGTERM))
    except ProcessLookupError:
        pass
    except Exception:
        return unknown('sigterm_failed', signals=signals, members=members)

    deadline = monotonic() + term_grace_s
    while True:
        try:
            members = snapshot()
        except Exception:
            return unknown('process_group_identity_changed_after_term',
                           signals=signals)
        if not members:
            return {'schema':_CLEANUP_SCHEMA,'status':'terminated',
                'verified_empty':True,'clean_exit_verified':False,
                'signals_sent':signals,'members':[],
                'task_success':None,'replay_allowed':False}
        remaining = deadline - monotonic()
        if remaining <= 0:
            break
        sleep(min(0.01, remaining))

    # Revalidate immediately before escalation. Unknown/reused members refuse.
    try:
        members = snapshot()
    except Exception:
        return unknown('process_group_identity_changed_before_kill',
                       signals=signals)
    if not members:
        return {'schema':_CLEANUP_SCHEMA,'status':'terminated',
            'verified_empty':True,'clean_exit_verified':False,
            'signals_sent':signals,'members':[],
            'task_success':None,'replay_allowed':False}
    try:
        killpg(pgid, _SIGKILL)
        signals.append(_signal_label(_SIGKILL))
    except ProcessLookupError:
        pass
    except Exception:
        return unknown('sigkill_failed', signals=signals, members=members)

    deadline = monotonic() + kill_settle_s
    while True:
        try:
            members = snapshot()
        except Exception:
            return unknown('process_group_identity_changed_after_kill',
                           signals=signals)
        if not members:
            return {'schema':_CLEANUP_SCHEMA,'status':'killed',
                'verified_empty':True,'clean_exit_verified':False,
                'signals_sent':signals,'members':[],
                'task_success':None,'replay_allowed':False}
        remaining = deadline - monotonic()
        if remaining <= 0:
            return unknown('process_group_not_empty_after_kill',
                           signals=signals, members=members)
        sleep(min(0.01, remaining))
