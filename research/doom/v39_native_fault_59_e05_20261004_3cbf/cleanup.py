"""Research observer cleanup: retain each failure and continue result writing."""


def close_resources(handles, result):
    for handle in handles:
        try:
            handle.close()
        except Exception as exc:
            result['cleanup_faults'].append(type(exc).__name__ + ': ' + repr(exc))
