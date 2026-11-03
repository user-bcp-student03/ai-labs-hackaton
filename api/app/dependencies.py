import sqlite3

from fastapi import Request


def get_db_connection(request: Request) -> sqlite3.Connection:
    return request.app.state.connection
