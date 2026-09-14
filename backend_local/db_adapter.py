import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Render ve bazı platformlar "postgres://" verir, psycopg2 "postgresql://" bekler
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

class UniversalRow(dict):
    """Hem sözlük hem de indeksle (row[0], row['name']) erişilebilen satır sarmalayıcısı."""
    def __init__(self, cursor, row):
        super().__init__()
        self._keys = [col[0] for col in cursor.description]
        self._values = row
        for k, v in zip(self._keys, row):
            self[k] = v

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._values[item]
        return super().__getitem__(item)

class PostgresConnectionWrapper:
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor(), self._conn)

    def execute(self, query, params=None):
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

class PostgresCursorWrapper:
    def __init__(self, pg_cursor, pg_conn=None):
        self._cursor = pg_cursor
        self._conn = pg_conn
        self.lastrowid = None

    def execute(self, query, params=None):
        # SQLite '?' işaretlerini PostgreSQL '%s' işaretine dönüştür
        pg_query = query.replace("?", "%s")
        # SQLite IF NOT EXISTS ve AUTOINCREMENT uyumluluğu
        if "AUTOINCREMENT" in pg_query:
            pg_query = pg_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        if "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" in pg_query:
            pg_query = pg_query.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "TIMESTAMP DEFAULT NOW()")

        # PostgreSQL ON CONFLICT dönüşümleri
        upper_q = pg_query.strip().upper()
        if upper_q.startswith("INSERT OR IGNORE INTO"):
            pg_query = pg_query.replace("INSERT OR IGNORE INTO", "INSERT INTO", 1).replace("insert or ignore into", "INSERT INTO", 1)
            pg_query += " ON CONFLICT DO NOTHING"
        elif upper_q.startswith("INSERT OR REPLACE INTO EXPORT_SETTINGS"):
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO", 1).replace("insert or replace into", "INSERT INTO", 1)
            pg_query += " ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
        elif upper_q.startswith("INSERT OR REPLACE INTO DEVICE_TOKENS"):
            pg_query = pg_query.replace("INSERT OR REPLACE INTO", "INSERT INTO", 1).replace("insert or replace into", "INSERT INTO", 1)
            pg_query += " ON CONFLICT (token) DO UPDATE SET device_type = EXCLUDED.device_type"

        try:
            if params is None:
                self._cursor.execute(pg_query)
            else:
                self._cursor.execute(pg_query, params)
            
            # Eğer INSERT yapıldıysa ve RETURNING yoksa lastrowid'yi yakalamaya çalış
            if pg_query.strip().upper().startswith("INSERT"):
                try:
                    self._cursor.execute("SELECT LASTVAL()")
                    row = self._cursor.fetchone()
                    if row:
                        self.lastrowid = row[0]
                except Exception:
                    pass
        except Exception as e:
            if self._conn:
                try:
                    self._conn.rollback()
                except Exception:
                    pass
            raise e
        return self

    def executemany(self, query, seq_of_parameters):
        for params in seq_of_parameters:
            self.execute(query, params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return UniversalRow(self._cursor, row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [UniversalRow(self._cursor, r) for r in rows]

    @property
    def description(self):
        return self._cursor.description


def get_universal_db(sqlite_path):
    """
    Ortamda DATABASE_URL (PostgreSQL) varsa ona bağlanır,
    yoksa yerel SQLite veritabanını kullanır.
    """
    if DATABASE_URL:
        try:
            import psycopg2
            pg_conn = psycopg2.connect(DATABASE_URL)
            return PostgresConnectionWrapper(pg_conn)
        except Exception as e:
            print(f"PostgreSQL bağlantı hatası, SQLite'a dönülüyor: {e}")

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn
