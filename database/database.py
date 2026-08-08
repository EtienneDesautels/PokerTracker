import sqlite3
from pathlib import Path
from typing import Any


DB_NAME = (
    Path(__file__).resolve().parent.parent
    / "tracker.db"
)


class Database:
    def __init__(
        self,
        db_path: str | Path = DB_NAME
    ):
        self.db_path = str(
            db_path
        )

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.db_path
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def create_tables(self) -> None:
        with self.connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cash_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cash_hands (
                    hand_id TEXT PRIMARY KEY,
                    date TEXT,
                    limite TEXT,
                    sb REAL NOT NULL,
                    bb REAL NOT NULL,
                    profit REAL NOT NULL,
                    profit_bb REAL NOT NULL,
                    session_id INTEGER,

                    FOREIGN KEY (session_id)
                        REFERENCES cash_sessions(session_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    tournament_id TEXT PRIMARY KEY,
                    date TEXT,
                    buyin REAL NOT NULL,
                    rake REAL NOT NULL,
                    prize REAL NOT NULL,
                    profit REAL NOT NULL,
                    place INTEGER,
                    players INTEGER
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

    def initialize_bankroll(
        self,
        bankroll: float
    ) -> None:
        self.set_setting(
            key="starting_bankroll",
            value=bankroll,
            overwrite=False
        )

    def get_setting(
        self,
        key: str
    ) -> str | None:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                SELECT value
                FROM settings
                WHERE key = ?
                """,
                (key,)
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return str(
            row["value"]
        )

    def set_setting(
        self,
        key: str,
        value: Any,
        overwrite: bool = True
    ) -> None:
        with self.connect() as connection:
            if overwrite:
                connection.execute(
                    """
                    INSERT INTO settings (
                        key,
                        value
                    )
                    VALUES (?, ?)

                    ON CONFLICT(key)
                    DO UPDATE SET
                        value = excluded.value
                    """,
                    (
                        key,
                        str(value)
                    )
                )

            else:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO settings (
                        key,
                        value
                    )
                    VALUES (?, ?)
                    """,
                    (
                        key,
                        str(value)
                    )
                )

    def insert_cash_hand(
        self,
        hand: dict
    ) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO cash_hands (
                    hand_id,
                    date,
                    limite,
                    sb,
                    bb,
                    profit,
                    profit_bb,
                    session_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hand["hand_id"],
                    hand["date"],
                    hand["limite"],
                    hand["sb"],
                    hand["bb"],
                    hand["profit"],
                    hand["profit_bb"],
                    hand.get("session_id")
                )
            )

            return cursor.rowcount > 0

    def cash_hand_exists(
        self,
        hand_id: str
    ) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                SELECT 1
                FROM cash_hands
                WHERE hand_id = ?
                LIMIT 1
                """,
                (hand_id,)
            )

            return cursor.fetchone() is not None

    def insert_tournament(
        self,
        tournament: dict
    ) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO tournaments (
                    tournament_id,
                    date,
                    buyin,
                    rake,
                    prize,
                    profit,
                    place,
                    players
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tournament["tournament_id"],
                    tournament["date"],
                    tournament["buyin"],
                    tournament["rake"],
                    tournament["prize"],
                    tournament["profit"],
                    tournament["place"],
                    tournament["players"]
                )
            )

            return cursor.rowcount > 0

    def tournament_exists(
        self,
        tournament_id: str
    ) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                SELECT 1
                FROM tournaments
                WHERE tournament_id = ?
                LIMIT 1
                """,
                (tournament_id,)
            )

            return cursor.fetchone() is not None

    def get_cash_stats(self) -> dict:
        with self.connect() as connection:
            cursor = connection.execute("""
                SELECT
                    COUNT(*) AS hands,
                    COALESCE(
                        SUM(profit),
                        0
                    ) AS profit,
                    COALESCE(
                        SUM(profit_bb),
                        0
                    ) AS profit_bb
                FROM cash_hands
            """)

            row = cursor.fetchone()

        hands = int(
            row["hands"]
        )

        profit = float(
            row["profit"]
        )

        profit_bb = float(
            row["profit_bb"]
        )

        bb100 = 0.0

        if hands > 0:
            bb100 = (
                profit_bb
                / hands
                * 100
            )

        return {
            "hands": hands,
            "profit": profit,
            "profit_bb": profit_bb,
            "bb100": bb100
        }

    def get_tournament_stats(self) -> dict:
        with self.connect() as connection:
            cursor = connection.execute("""
                SELECT
                    COUNT(*) AS tournaments,

                    COALESCE(
                        SUM(buyin + rake),
                        0
                    ) AS total_cost,

                    COALESCE(
                        SUM(prize),
                        0
                    ) AS total_prizes,

                    COALESCE(
                        SUM(profit),
                        0
                    ) AS profit,

                    COALESCE(
                        AVG(buyin + rake),
                        0
                    ) AS average_buyin,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN prize > 0
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS itm_count,

                    COALESCE(
                        MAX(prize),
                        0
                    ) AS best_prize

                FROM tournaments
            """)

            row = cursor.fetchone()

        tournaments = int(
            row["tournaments"]
        )

        total_cost = float(
            row["total_cost"]
        )

        total_prizes = float(
            row["total_prizes"]
        )

        profit = float(
            row["profit"]
        )

        average_buyin = float(
            row["average_buyin"]
        )

        itm_count = int(
            row["itm_count"]
        )

        best_prize = float(
            row["best_prize"]
        )

        roi = 0.0
        itm_rate = 0.0

        if total_cost > 0:
            roi = (
                profit
                / total_cost
                * 100
            )

        if tournaments > 0:
            itm_rate = (
                itm_count
                / tournaments
                * 100
            )

        return {
            "tournaments": tournaments,
            "total_cost": total_cost,
            "total_prizes": total_prizes,
            "profit": profit,
            "roi": roi,
            "average_buyin": average_buyin,
            "itm_count": itm_count,
            "itm_rate": itm_rate,
            "best_prize": best_prize
        }

    def get_current_bankroll(self) -> float:
        starting_value = self.get_setting(
            "starting_bankroll"
        )

        starting_bankroll = float(
            starting_value or 0
        )

        cash_stats = self.get_cash_stats()

        tournament_stats = (
            self.get_tournament_stats()
        )

        return (
            starting_bankroll
            + cash_stats["profit"]
            + tournament_stats["profit"]
        )

    def get_last_cash_hand(
        self
    ) -> dict | None:
        with self.connect() as connection:
            cursor = connection.execute("""
                SELECT
                    hand_id,
                    date,
                    session_id
                FROM cash_hands
                ORDER BY datetime(date) DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "hand_id": row["hand_id"],
            "date": row["date"],
            "session_id": row["session_id"]
        }

    def create_cash_session(
        self,
        started_at: str
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO cash_sessions (
                    started_at,
                    ended_at
                )
                VALUES (?, ?)
                """,
                (
                    started_at,
                    started_at
                )
            )

            return int(
                cursor.lastrowid
            )

    def update_cash_session_end(
        self,
        session_id: int,
        ended_at: str
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE cash_sessions
                SET ended_at = ?
                WHERE session_id = ?
                """,
                (
                    ended_at,
                    session_id
                )
            )

    def get_current_session_stats(
        self
    ) -> dict:
        with self.connect() as connection:
            cursor = connection.execute("""
                SELECT
                    s.session_id,
                    s.started_at,
                    s.ended_at,
                    COUNT(h.hand_id) AS hands,

                    COALESCE(
                        SUM(h.profit),
                        0
                    ) AS profit,

                    COALESCE(
                        SUM(h.profit_bb),
                        0
                    ) AS profit_bb

                FROM cash_sessions AS s

                LEFT JOIN cash_hands AS h
                    ON h.session_id = s.session_id

                WHERE s.session_id = (
                    SELECT MAX(session_id)
                    FROM cash_sessions
                )

                GROUP BY
                    s.session_id,
                    s.started_at,
                    s.ended_at
            """)

            row = cursor.fetchone()

        if row is None:
            return {
                "session_id": None,
                "started_at": None,
                "ended_at": None,
                "hands": 0,
                "profit": 0.0,
                "profit_bb": 0.0,
                "bb100": 0.0
            }

        hands = int(
            row["hands"]
        )

        profit = float(
            row["profit"]
        )

        profit_bb = float(
            row["profit_bb"]
        )

        bb100 = 0.0

        if hands > 0:
            bb100 = (
                profit_bb
                / hands
                * 100
            )

        return {
            "session_id": int(
                row["session_id"]
            ),
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "hands": hands,
            "profit": profit,
            "profit_bb": profit_bb,
            "bb100": bb100
        }


database = Database()


def connect() -> sqlite3.Connection:
    return database.connect()


def create_tables() -> None:
    database.create_tables()


def initialize_bankroll(
    bankroll: float
) -> None:
    database.initialize_bankroll(
        bankroll
    )


def get_setting(
    key: str
) -> str | None:
    return database.get_setting(
        key
    )


def set_setting(
    key: str,
    value: Any
) -> None:
    database.set_setting(
        key,
        value
    )


def insert_cash_hand(
    hand: dict
) -> bool:
    return database.insert_cash_hand(
        hand
    )


def get_cash_stats() -> dict:
    return database.get_cash_stats()


def get_tournament_stats() -> dict:
    return database.get_tournament_stats()


def get_current_bankroll() -> float:
    return database.get_current_bankroll()


def get_current_session_stats() -> dict:
    return database.get_current_session_stats()