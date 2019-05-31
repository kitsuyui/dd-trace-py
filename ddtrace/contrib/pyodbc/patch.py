# 3p
import pyodbc

# project
from ddtrace.vendor import wrapt
from ddtrace.contrib.dbapi import TracedConnection, TracedCursor, FetchTracedCursor
from ddtrace.ext import AppTypes
from ddtrace.pin import Pin
from ddtrace.settings import config

# Original connect method
_connect = pyodbc.connect


def patch():
    wrapped = wrapt.FunctionWrapper(_connect, traced_connect)
    setattr(pyodbc, 'connect', wrapped)


def unpatch():
    pyodbc.connect = _connect


def traced_connect(func, _, args, kwargs):
    conn = func(*args, **kwargs)
    return patch_conn(conn)


def patch_conn(conn):
    wrapped = TracedPyODBC(conn)
    Pin(service='pyodbc', app='pyodbc', app_type=AppTypes.db).onto(wrapped)
    return wrapped


class TracedPyODBCCursor(TracedCursor):
    def executemany(self, *args, **kwargs):
        # DEV: PyODBC Cursor.execute always returns back the cursor instance
        super(TracedPyODBCCursor, self).executemany(*args, **kwargs)
        return self

    def execute(self, *args, **kwargs):
        # DEV: PyODBC Cursor.execute always returns back the cursor instance
        super(TracedPyODBCCursor, self).execute(*args, **kwargs)
        return self


class TracedPyODBCFetchCursor(TracedPyODBCCursor, FetchTracedCursor):
    pass


class TracedPyODBC(TracedConnection):
    def __init__(self, conn, pin=None, cursor_cls=None):
        if not cursor_cls:
            # Do not trace `fetch*` methods by default
            cursor_cls = TracedPyODBCCursor

            super(TracedPyODBC, self).__init__(conn, pin=pin, cursor_cls=cursor_cls)

    def execute(self, *args, **kwargs):
        # pyodbc has a few extra sugar functions
        return self.execute(*args, **kwargs)
