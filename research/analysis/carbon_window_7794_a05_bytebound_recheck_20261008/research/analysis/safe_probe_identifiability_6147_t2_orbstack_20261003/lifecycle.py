"""Narrow cleanup contract shared by the GUI controller and host tests."""


def close_display(display_client, connection_closed_error):
    try:
        display_client.close()
    except connection_closed_error:
        # A fixture may terminate Xvfb immediately after its final reset.
        # Callers must not use this helper around observation or input work.
        pass
