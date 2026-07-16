from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import DestinationPack, PlanningSession, TravelerProfile, TripResult


class Database:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trips (
                    id TEXT PRIMARY KEY,
                    request_payload TEXT NOT NULL,
                    result_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS planning_sessions (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS planning_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES planning_sessions(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS destination_packs (
                    slug TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def get_profile(self) -> TravelerProfile | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM profile WHERE id = 1").fetchone()
        return TravelerProfile.model_validate_json(row["payload"]) if row else None

    def save_profile(self, profile: TravelerProfile) -> TravelerProfile:
        if not profile.consent_to_store:
            self.delete_profile()
            return profile
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO profile(id, payload, updated_at) VALUES(1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (profile.model_dump_json(), profile.updated_at.isoformat()),
            )
        return profile

    def delete_profile(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM profile WHERE id = 1")

    def save_trip(self, result: TripResult) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO trips(id, request_payload, result_payload, updated_at) VALUES(?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET request_payload=excluded.request_payload, "
                "result_payload=excluded.result_payload, updated_at=excluded.updated_at",
                (
                    result.id,
                    result.request.model_dump_json(),
                    result.model_dump_json(),
                    result.updated_at.isoformat(),
                ),
            )

    def get_trip(self, trip_id: str) -> TripResult | None:
        with self._connect() as connection:
            row = connection.execute("SELECT result_payload FROM trips WHERE id = ?", (trip_id,)).fetchone()
        return TripResult.model_validate_json(row["result_payload"]) if row else None

    def save_planning_session(self, session: PlanningSession) -> PlanningSession:
        if not session.consent_to_store:
            return session
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO planning_sessions(id, payload, created_at, updated_at) VALUES(?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (session.id, session.model_dump_json(), session.created_at.isoformat(), session.updated_at.isoformat()),
            )
            connection.execute("DELETE FROM planning_messages WHERE session_id = ?", (session.id,))
            connection.executemany(
                "INSERT INTO planning_messages(session_id, role, content, created_at) VALUES(?, ?, ?, ?)",
                [(session.id, message.role, message.content, message.created_at.isoformat()) for message in session.messages],
            )
        return session

    def get_planning_session(self, session_id: str) -> PlanningSession | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM planning_sessions WHERE id = ?", (session_id,)).fetchone()
        return PlanningSession.model_validate_json(row["payload"]) if row else None

    def delete_planning_session(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM planning_messages WHERE session_id = ?", (session_id,))
            connection.execute("DELETE FROM planning_sessions WHERE id = ?", (session_id,))

    def save_destination_pack(self, pack: DestinationPack) -> DestinationPack:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO destination_packs(slug, payload, status, updated_at) VALUES(?, ?, ?, ?) "
                "ON CONFLICT(slug) DO UPDATE SET payload=excluded.payload, status=excluded.status, updated_at=excluded.updated_at",
                (pack.slug, pack.model_dump_json(), pack.status, pack.updated_at.isoformat()),
            )
        return pack

    def get_destination_pack(self, slug: str) -> DestinationPack | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM destination_packs WHERE slug = ?", (slug,)).fetchone()
        return DestinationPack.model_validate_json(row["payload"]) if row else None

    def list_destination_packs(self) -> list[DestinationPack]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM destination_packs ORDER BY updated_at DESC").fetchall()
        return [DestinationPack.model_validate_json(row["payload"]) for row in rows]
