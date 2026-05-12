import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "token_usage.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         TEXT NOT NULL,
            model      TEXT NOT NULL,
            input_tok  INTEGER NOT NULL,
            output_tok INTEGER NOT NULL,
            project    TEXT,
            session_id TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_usage(model, input_tok, output_tok, project=None, session_id=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO usage (ts, model, input_tok, output_tok, project, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), model, input_tok, output_tok, project, session_id))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
