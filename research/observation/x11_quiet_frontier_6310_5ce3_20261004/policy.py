def classify(covered, barrier, events):
    status = 'UNKNOWN_NO_COVERAGE'
    if covered is True and barrier is True:
        status = 'CHANGE_OBSERVED' if events else 'QUIET_AS_OF_FRONTIER'
    return {'historical':status,'authority':False}
