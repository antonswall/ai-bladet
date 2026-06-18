#!/usr/bin/env python3
"""
AI-Bladet — Seen-databas (Pipeline Steg 0)
============================================
Håller koll på alla tidigare publicerade/insamlade nyheter
för att undvika dubbletter mellan veckor.

SQLite-baserad. Används av collect.py för att filtrera bort
redan sedda kandidater.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class SeenDB:
    """SQLite-databas över sedda/publicerade nyheter."""

    def __init__(self, db_path: str | Path = None):
        if db_path is None:
            db_path = Path(__file__).parent / "seen.db"
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
        return self._conn

    def init(self):
        """Skapa tabeller om de inte finns."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_items (
                content_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                seen_count INTEGER DEFAULT 1,
                status TEXT DEFAULT 'new',
                published_week TEXT
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_seen_status
            ON seen_items(status)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_seen_published_week
            ON seen_items(published_week)
        """)
        self.conn.commit()

    def is_seen(self, content_hash: str) -> bool:
        """Kolla om en hash redan finns i databasen."""
        row = self.conn.execute(
            "SELECT 1 FROM seen_items WHERE content_hash = ?",
            (content_hash,)
        ).fetchone()
        return row is not None

    def get_all_hashes(self) -> set[str]:
        """Hämta alla hash-värden."""
        rows = self.conn.execute("SELECT content_hash FROM seen_items").fetchall()
        return {r[0] for r in rows}

    def get_published_hashes(self) -> set[str]:
        """Hämta hash-värden för publicerade artiklar."""
        rows = self.conn.execute(
            "SELECT content_hash FROM seen_items WHERE status = 'published'"
        ).fetchall()
        return {r[0] for r in rows}

    def mark_seen(self, content_hash: str, url: str, title: str = ""):
        """Markera en hash som sedd (första gången) eller uppdatera."""
        now = datetime.now(timezone.utc).isoformat()
        existing = self.conn.execute(
            "SELECT seen_count, first_seen, status FROM seen_items WHERE content_hash = ?",
            (content_hash,)
        ).fetchone()

        if existing:
            # Uppdatera
            new_count = existing[0] + 1
            # Behåll published-status — publicerade artiklar förblir publicerade
            self.conn.execute(
                """UPDATE seen_items
                   SET last_seen = ?, seen_count = ?, url = ?, title = ?
                   WHERE content_hash = ?""",
                (now, new_count, url, title, content_hash)
            )
        else:
            # Ny
            self.conn.execute(
                """INSERT INTO seen_items (content_hash, url, title, first_seen, last_seen)
                   VALUES (?, ?, ?, ?, ?)""",
                (content_hash, url, title, now, now)
            )

    def mark_seen_batch(self, items: list[dict]):
        """Markera flera objekt som sedda (bulk-insert)."""
        now = datetime.now(timezone.utc).isoformat()
        with self.conn:
            for item in items:
                self.mark_seen(
                    item["content_hash"],
                    item.get("url", ""),
                    item.get("title", "")
                )

    def mark_published(self, week: str, hashes: list[str]):
        """Markera artiklar som publicerade i en specifik vecka."""
        with self.conn:
            self.conn.executemany(
                """UPDATE seen_items
                   SET status = 'published', published_week = ?
                   WHERE content_hash = ?""",
                [(week, h) for h in hashes]
            )

    def mark_skipped(self, hashes: list[str]):
        """Markera artiklar som överhoppade (sågs men valdes bort)."""
        with self.conn:
            self.conn.executemany(
                "UPDATE seen_items SET status = 'skipped' WHERE content_hash = ?",
                [(h,) for h in hashes]
            )

    def get_stats(self) -> dict:
        """Hämta statistik."""
        total = self.conn.execute("SELECT COUNT(*) FROM seen_items").fetchone()[0]
        published = self.conn.execute(
            "SELECT COUNT(*) FROM seen_items WHERE status = 'published'"
        ).fetchone()[0]
        new_count = self.conn.execute(
            "SELECT COUNT(*) FROM seen_items WHERE status = 'new'"
        ).fetchone()[0]
        return {
            "total_seen": total,
            "total_published": published,
            "total_new": new_count,
        }

    def prune_old(self, days: int = 90):
        """Ta bort artiklar äldre än X dagar som inte publicerats."""
        cutoff = datetime.now(timezone.utc)
        # Behåll publicerade artiklar för alltid
        self.conn.execute(
            """DELETE FROM seen_items
               WHERE status != 'published'
               AND last_seen < ?""",
            (cutoff,)
        )
        self.conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# ─── CLI för manuell administration ──────────────────────────────────────────

if __name__ == "__main__":
    import sys

    db = SeenDB()
    db.init()

    if len(sys.argv) < 2:
        stats = db.get_stats()
        print(f"SeenDB — {db.db_path}")
        print(f"  Totalt sedda:  {stats['total_seen']}")
        print(f"  Publicerade:   {stats['total_published']}")
        print(f"  Nya (osedda):  {stats['total_new']}")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "prune":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        db.prune_old(days)
        print(f"Prunade poster äldre än {days} dagar (ej publicerade)")

    elif cmd == "clear":
        db.conn.execute("DELETE FROM seen_items")
        db.conn.commit()
        print("Rensade hela seen-databasen")

    elif cmd == "init":
        db.init()
        print("Initierade databasen")

    db.close()
