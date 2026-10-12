"""Klasse Datenbank: SQLite-Zugriff für Druckerprofile, Regeln, Exportläufe (Stufe 2)."""

import sqlite3
from pathlib import Path


class Datenbank:
    """Verwaltet die SQLite-Datenbank für IFC2Print."""

    def __init__(self, db_pfad: Path):
        self.db_pfad = db_pfad
        self.conn: sqlite3.Connection | None = None

    def verbinden(self) -> None:
        """Öffnet die Datenbankverbindung und legt Schema an, falls nötig."""
        self.conn = sqlite3.connect(self.db_pfad)
        self.conn.row_factory = sqlite3.Row
        self._schema_anlegen()

    def _schema_anlegen(self) -> None:
        schema_pfad = Path(__file__).parent / "schema.sql"
        if schema_pfad.exists():
            self.conn.executescript(schema_pfad.read_text(encoding="utf-8"))
            self.conn.commit()

    def schliessen(self) -> None:
        if self.conn:
            self.conn.close()
