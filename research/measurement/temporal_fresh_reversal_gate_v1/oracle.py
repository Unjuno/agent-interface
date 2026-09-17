def expected(history_dir,fresh_dir):
    if not isinstance(history_dir,int) or isinstance(history_dir,bool) or history_dir not in (-1,1):
        return 'YIELD_UNKNOWN'
    if not isinstance(fresh_dir,int) or isinstance(fresh_dir,bool) or fresh_dir not in (-1,1):
        return 'YIELD_UNKNOWN'
    # Separately structured sign-of-product oracle.
    return 'CONTINUE' if history_dir*fresh_dir > 0 else 'YIELD_REVERSAL'
