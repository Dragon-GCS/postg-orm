from asyncpg.connection import Connection as PgConn, connect as pg_connect

class Connection:
    def __init__(self, conn: PgConn):
        self.conn = conn

    def __getattr__(self, name):
        return getattr(self.conn, name)


async def connect(*args, **kwargs) -> Connection:
    conn = await pg_connect(*args, **kwargs)
    return Connection(conn)