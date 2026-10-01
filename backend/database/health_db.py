"""
health_db.py — Full SQLite database layer
Tables: users, history, reports, chat_sessions
"""

import json
import sqlite3
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent / "health_assistant.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    c = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            last_login  TEXT
        )
    """)

    # ── Health history (predictions) ───────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id              TEXT PRIMARY KEY,
            user_id         TEXT,
            created_at      TEXT NOT NULL,
            domain          TEXT NOT NULL DEFAULT 'human',
            symptoms        TEXT NOT NULL DEFAULT '[]',
            disease         TEXT NOT NULL DEFAULT '',
            confidence      INTEGER NOT NULL DEFAULT 0,
            risk_level      TEXT NOT NULL DEFAULT 'low',
            emergency       INTEGER NOT NULL DEFAULT 0,
            doctor_type     TEXT NOT NULL DEFAULT '',
            additional_info TEXT NOT NULL DEFAULT '{}'
        )
    """)

    # ── Uploaded reports ───────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id          TEXT PRIMARY KEY,
            user_id     TEXT,
            created_at  TEXT NOT NULL,
            filename    TEXT NOT NULL,
            file_type   TEXT NOT NULL,
            ocr_text    TEXT,
            analysis    TEXT NOT NULL DEFAULT '{}'
        )
    """)

    # ── Chat sessions ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT,
            created_at  TEXT NOT NULL,
            messages    TEXT NOT NULL DEFAULT '[]',
            final_diagnosis TEXT
        )
    """)

    # ── Token blacklist (for logout / revocation) ──────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS token_blacklist (
            token      TEXT PRIMARY KEY,
            expires_at INTEGER NOT NULL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_blacklist_exp ON token_blacklist(expires_at)")

    # ── Migrations: add columns to existing tables if missing ─────────────────
    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(history)")}
    if "user_id" not in existing_cols:
        c.execute("ALTER TABLE history ADD COLUMN user_id TEXT")
    if "report_type" not in existing_cols:
        c.execute("ALTER TABLE history ADD COLUMN report_type TEXT NOT NULL DEFAULT ''")
    if "source" not in existing_cols:
        c.execute("ALTER TABLE history ADD COLUMN source TEXT NOT NULL DEFAULT 'chat'")

    # ── Indexes (safe to re-run) ───────────────────────────────────────────────
    c.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    conn.commit()
    conn.close()


# ── User operations ────────────────────────────────────────────────────────────

def create_user(name: str, email: str, password_hash: str) -> str:
    conn = get_connection()
    c = conn.cursor()
    user_id = f"usr_{int(datetime.utcnow().timestamp() * 1000)}"
    c.execute(
        "INSERT INTO users (id, name, email, password_hash, created_at) VALUES (?,?,?,?,?)",
        (user_id, name, email.lower().strip(), password_hash, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, email, created_at, last_login FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_last_login(user_id: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET last_login = ? WHERE id = ?",
                 (datetime.utcnow().isoformat(), user_id))
    conn.commit()
    conn.close()


def update_user_profile(user_id: str, name: str, password_hash: Optional[str]) -> None:
    conn = get_connection()
    if password_hash:
        conn.execute("UPDATE users SET name = ?, password_hash = ? WHERE id = ?",
                     (name, password_hash, user_id))
    else:
        conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    conn.close()


# ── History operations ─────────────────────────────────────────────────────────

def save_history(record: Dict[str, Any]) -> str:
    conn = get_connection()
    c = conn.cursor()
    record_id = record.get("id") or f"hist_{int(datetime.utcnow().timestamp() * 1000)}"
    additional = record.get("additional_info", {})
    source = additional.get("source", record.get("source", "chat"))
    report_type = additional.get("report_type", record.get("report_type", ""))
    c.execute(
        """INSERT OR REPLACE INTO history
           (id, user_id, created_at, domain, symptoms, disease, confidence,
            risk_level, emergency, doctor_type, additional_info, source, report_type)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            record_id,
            record.get("user_id"),
            datetime.utcnow().isoformat(),
            record.get("domain", "human"),
            json.dumps(record.get("symptoms", []), ensure_ascii=False),
            record.get("disease", ""),
            int(record.get("confidence", 0)),
            record.get("risk_level", "low"),
            1 if record.get("emergency") else 0,
            record.get("doctor_type", ""),
            json.dumps(additional, ensure_ascii=False),
            source,
            report_type,
        ),
    )
    conn.commit()
    conn.close()
    return record_id


def get_history(limit: int = 100, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    if user_id:
        c.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
    else:
        c.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [_row_to_history(row) for row in rows]


def get_history_item(history_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE id = ?", (history_id,))
    row = c.fetchone()
    conn.close()
    return _row_to_history(row) if row else None


def get_history_stats(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Return aggregated stats for the dashboard."""
    conn = get_connection()
    c = conn.cursor()
    base = "WHERE user_id = ?" if user_id else ""
    params = (user_id,) if user_id else ()

    c.execute(f"SELECT COUNT(*) FROM history {base}", params)
    total = c.fetchone()[0]

    c.execute(f"SELECT COUNT(*) FROM history {base} {'AND' if user_id else 'WHERE'} risk_level='low'",
              params)
    low = c.fetchone()[0]

    c.execute(f"SELECT COUNT(*) FROM history {base} {'AND' if user_id else 'WHERE'} risk_level='medium'",
              params)
    medium = c.fetchone()[0]

    c.execute(f"SELECT COUNT(*) FROM history {base} {'AND' if user_id else 'WHERE'} risk_level='high'",
              params)
    high = c.fetchone()[0]

    c.execute(f"SELECT COUNT(*) FROM history {base} {'AND' if user_id else 'WHERE'} emergency=1",
              params)
    emergencies = c.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "low_risk": low,
        "medium_risk": medium,
        "high_risk": high,
        "emergencies": emergencies,
    }


def _row_to_history(row) -> Dict[str, Any]:
    return {
        "id":           row["id"],
        "user_id":      row["user_id"],
        "created_at":   row["created_at"],
        "domain":       row["domain"],
        "symptoms":     json.loads(row["symptoms"] or "[]"),
        "disease":      row["disease"],
        "confidence":   row["confidence"],
        "risk_level":   row["risk_level"],
        "emergency":    bool(row["emergency"]),
        "doctor_type":  row["doctor_type"],
        "additional_info": json.loads(row["additional_info"] or "{}"),
        "source":       row["source"] if "source" in row.keys() else "chat",
        "report_type":  row["report_type"] if "report_type" in row.keys() else "",
    }


# ── Report operations ──────────────────────────────────────────────────────────

def save_report(record: Dict[str, Any]) -> str:
    conn = get_connection()
    c = conn.cursor()
    report_id = f"rpt_{int(datetime.utcnow().timestamp() * 1000)}"
    c.execute(
        """INSERT INTO reports (id, user_id, created_at, filename, file_type, ocr_text, analysis)
           VALUES (?,?,?,?,?,?,?)""",
        (
            report_id,
            record.get("user_id"),
            datetime.utcnow().isoformat(),
            record.get("filename", ""),
            record.get("file_type", ""),
            record.get("ocr_text", ""),
            json.dumps(record.get("analysis", {}), ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()
    return report_id


# ── Token blacklist operations (Task 15) ─────────────────────────────────────

import time as _time


def add_token_blacklist(token: str, expires_at: int) -> None:
    """Blacklist a JWT so it cannot be reused after logout."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO token_blacklist (token, expires_at) VALUES (?, ?)",
        (token, expires_at),
    )
    # Prune already-expired tokens to keep the table small
    conn.execute("DELETE FROM token_blacklist WHERE expires_at < ?", (int(_time.time()),))
    conn.commit()
    conn.close()


def is_token_blacklisted(token: str) -> bool:
    """Return True if the token has been revoked via logout."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM token_blacklist WHERE token = ?", (token,))
    found = c.fetchone() is not None
    conn.close()
    return found


# ── Init on import ─────────────────────────────────────────────────────────────
init_db()
