"""Fail closed on missing or non-neutral action release evidence."""


def completed_neutral(receipt):
    if not isinstance(receipt, dict) or receipt.get('status') != 'completed':
        return False
    execution = receipt.get('execution')
    if not isinstance(execution, dict):
        return False
    releases = execution.get('releases')
    return (isinstance(releases, list) and bool(releases)
            and all(isinstance(item, dict) and item.get('verified') is True
                    and item.get('keys_down') == [] and item.get('buttons_down') == []
                    for item in releases))
