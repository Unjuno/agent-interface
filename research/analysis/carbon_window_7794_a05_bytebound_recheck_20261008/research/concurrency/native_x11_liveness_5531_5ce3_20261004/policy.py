def classify(timeout, terminal, valid, previous=None):
    if previous == 'FAILED' or terminal is True:
        return 'FAILED'
    if valid is True:
        return 'RESPONSIVE_SCOPED'
    if valid is False:
        return 'EVIDENCE_INVALID'
    return 'SUSPECTED_UNAVAILABLE' if timeout else 'UNKNOWN'
