"""Pure record conversion used by the #5156 formal X11 runner."""


def joined_release_record(row):
    """Tag an owner release row without colliding with its existing event."""
    return dict(row, event="joined_release")
