"""Instrument pyodbc to report pyodbc queries.

``patch_all`` will automatically patch your pyodbc connection to make it work.
::

    from ddtrace import Pin, patch
    import pyodbc

    patch(pyodbc=True)

    # This will report a span with the default settings
    db = pyodbc.connect(...)
    cursor = db.cursor()
    cursor.execute("select * from users where id = 1")

    # Use a pin to specify metadata related to this connection
    Pin.override(db, service='pyodbc-users')
"""
from .patch import patch

__all__ = ['connection_factory', 'patch']
