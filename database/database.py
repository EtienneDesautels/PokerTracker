import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


DB_NAME = (
    Path(__file__).resolve().parent.parent
    / "tracker.db"
)

SESSION_TIMEOUT = timedelta(minutes=20)


class Database:
    def __init__(
        self,
        db_path: str | Path = DB_NAME
    ):
        self.db_path = str(db_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.db_path
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    # =====================================================
    # CRÉATION DES TABLES
    # =====================================================

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
                CREATE TABLE IF NOT EXISTS mtt_corrections (
                    correction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    buyin_total REAL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Migration pour les anciennes bases où
            # mtt_corrections n'avait pas buyin_total.
            cursor.execute("""
                PRAGMA table_info(mtt_corrections)
            """)

            columns = [
                row["name"]
                for row in cursor.fetchall()
            ]

            if "buyin_total" not in columns:
                cursor.execute("""
                    ALTER TABLE mtt_corrections
                    ADD COLUMN buyin_total REAL
                """)

    # =====================================================
    # SETTINGS
    # =====================================================

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

    # =====================================================
    # CASH GAME — INSERTION
    # =====================================================

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

    # =====================================================
    # CASH GAME — FILTRES
    # =====================================================

    def get_cash_limits(self) -> list[str]:
        """
        Retourne seulement les limites réellement présentes
        dans la base.
        """

        with self.connect() as connection:
            cursor = connection.execute("""
                SELECT
                    limite,
                    MAX(bb) AS bb
                FROM cash_hands
                WHERE limite IS NOT NULL
                GROUP BY limite
                ORDER BY bb ASC
            """)

            rows = cursor.fetchall()

        return [
            str(row["limite"])
            for row in rows
        ]

    def get_cash_stats(
        self,
        limite: str | None = None
    ) -> dict:

        query = """
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
        """

        parameters = ()

        if limite is not None:
            query += """
                WHERE limite = ?
            """

            parameters = (
                limite,
            )

        with self.connect() as connection:
            cursor = connection.execute(
                query,
                parameters
            )

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
            "bb100": bb100,
            "limite": limite
        }

    # =====================================================
    # CASH GAME — SESSIONS
    # =====================================================

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
                WHERE date IS NOT NULL
                ORDER BY date DESC
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
        self,
        limite: str | None = None
    ) -> dict:
        """
        Détermine d'abord la dernière session globale.

        Ensuite, si une limite est sélectionnée,
        les statistiques sont calculées seulement
        avec les mains de cette limite dans la session.
        """

        with self.connect() as connection:
            cursor = connection.execute("""
                SELECT
                    hand_id,
                    date,
                    limite,
                    profit,
                    profit_bb,
                    session_id
                FROM cash_hands
                WHERE date IS NOT NULL
                ORDER BY date DESC
            """)

            rows = cursor.fetchall()

        if not rows:
            return self._empty_session_stats()

        full_session_rows = []

        previous_date = None

        for row in rows:

            try:
                current_date = datetime.fromisoformat(
                    row["date"]
                )

            except (
                ValueError,
                TypeError
            ):
                continue

            if previous_date is None:
                full_session_rows.append(
                    row
                )

                previous_date = current_date

                continue

            gap = (
                previous_date
                - current_date
            )

            if gap >= SESSION_TIMEOUT:
                break

            full_session_rows.append(
                row
            )

            previous_date = current_date

        if not full_session_rows:
            return self._empty_session_stats()

        session_started_at = (
            full_session_rows[-1]["date"]
        )

        session_ended_at = (
            full_session_rows[0]["date"]
        )

        if limite is None:
            filtered_rows = (
                full_session_rows
            )

        else:
            filtered_rows = [
                row
                for row in full_session_rows
                if row["limite"] == limite
            ]

        if not filtered_rows:
            return {
                "session_id": None,
                "started_at": session_started_at,
                "ended_at": session_ended_at,
                "hands": 0,
                "profit": 0.0,
                "profit_bb": 0.0,
                "bb100": 0.0
            }

        hands = len(
            filtered_rows
        )

        profit = sum(
            float(row["profit"])
            for row in filtered_rows
        )

        profit_bb = sum(
            float(row["profit_bb"])
            for row in filtered_rows
        )

        bb100 = 0.0

        if hands > 0:
            bb100 = (
                profit_bb
                / hands
                * 100
            )

        return {
            "session_id": filtered_rows[0]["session_id"],
            "started_at": session_started_at,
            "ended_at": session_ended_at,
            "hands": hands,
            "profit": profit,
            "profit_bb": profit_bb,
            "bb100": bb100
        }

    @staticmethod
    def _empty_session_stats() -> dict:
        return {
            "session_id": None,
            "started_at": None,
            "ended_at": None,
            "hands": 0,
            "profit": 0.0,
            "profit_bb": 0.0,
            "bb100": 0.0
        }

    # =====================================================
    # MTT — INSERTION
    # =====================================================

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
                (
                    tournament_id,
                )
            )

            return cursor.fetchone() is not None

    # =====================================================
    # MTT — BUY-INS DISPONIBLES
    # =====================================================

    def get_mtt_buyins(
        self
    ) -> list[float]:

        with self.connect() as connection:
            cursor = connection.execute("""
                SELECT DISTINCT
                    ROUND(
                        buyin + rake,
                        2
                    ) AS total_buyin
                FROM tournaments
                ORDER BY total_buyin ASC
            """)

            rows = cursor.fetchall()

        return [
            float(row["total_buyin"])
            for row in rows
        ]

    # =====================================================
    # MTT — CORRECTIONS
    # =====================================================

    def add_mtt_correction(
        self,
        date: str,
        amount: float,
        buyin_total: float | None = None
    ) -> None:

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO mtt_corrections (
                    date,
                    amount,
                    buyin_total
                )
                VALUES (?, ?, ?)
                """,
                (
                    date,
                    amount,
                    buyin_total
                )
            )

    def get_mtt_correction_total(
        self,
        buyin_total: float | None = None
    ) -> float:

        with self.connect() as connection:

            if buyin_total is None:
                cursor = connection.execute("""
                    SELECT
                        COALESCE(
                            SUM(amount),
                            0
                        ) AS total

                    FROM mtt_corrections
                """)

            else:
                cursor = connection.execute(
                    """
                    SELECT
                        COALESCE(
                            SUM(amount),
                            0
                        ) AS total

                    FROM mtt_corrections

                    WHERE ROUND(
                        buyin_total,
                        2
                    ) = ROUND(
                        ?,
                        2
                    )
                    """,
                    (
                        buyin_total,
                    )
                )

            row = cursor.fetchone()

        return float(
            row["total"]
        )

    # =====================================================
    # MTT — STATISTIQUES
    # =====================================================

    def get_tournament_stats(
        self,
        buyin_total: float | None = None
    ) -> dict:

        query = """
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
                ) AS imported_profit,

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
        """

        parameters = ()

        if buyin_total is not None:
            query += """
                WHERE ROUND(
                    buyin + rake,
                    2
                ) = ROUND(
                    ?,
                    2
                )
            """

            parameters = (
                buyin_total,
            )

        with self.connect() as connection:
            cursor = connection.execute(
                query,
                parameters
            )

            row = cursor.fetchone()

        tournaments = int(
            row["tournaments"]
        )

        total_cost = float(
            row["total_cost"]
        )

        imported_prizes = float(
            row["total_prizes"]
        )

        imported_profit = float(
            row["imported_profit"]
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

        correction_total = (
            self.get_mtt_correction_total(
                buyin_total
            )
        )

        real_profit = (
            imported_profit
            + correction_total
        )

        real_prizes = (
            imported_prizes
            + correction_total
        )

        roi = 0.0
        itm_rate = 0.0

        if total_cost > 0:
            roi = (
                real_profit
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
            "imported_prizes": imported_prizes,
            "total_prizes": real_prizes,
            "imported_profit": imported_profit,
            "corrections": correction_total,
            "profit": real_profit,
            "roi": roi,
            "average_buyin": average_buyin,
            "itm_count": itm_count,
            "itm_rate": itm_rate,
            "best_prize": best_prize,
            "buyin_filter": buyin_total
        }

    # =====================================================
    # BANKROLL
    # =====================================================

    def get_current_bankroll(
        self
    ) -> float:

        starting_value = self.get_setting(
            "starting_bankroll"
        )

        starting_bankroll = float(
            starting_value or 0
        )

        cash_stats = (
            self.get_cash_stats()
        )

        tournament_stats = (
            self.get_tournament_stats()
        )

        return (
            starting_bankroll
            + cash_stats["profit"]
            + tournament_stats["profit"]
        )


# =========================================================
# INSTANCE GLOBALE
# =========================================================

database = Database()


# =========================================================
# FONCTIONS DE COMPATIBILITÉ
# =========================================================

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


def get_cash_limits() -> list[str]:
    return database.get_cash_limits()


def get_cash_stats(
    limite: str | None = None
) -> dict:
    return database.get_cash_stats(
        limite
    )


def get_current_session_stats(
    limite: str | None = None
) -> dict:
    return database.get_current_session_stats(
        limite
    )


def get_mtt_buyins() -> list[float]:
    return database.get_mtt_buyins()


def get_tournament_stats(
    buyin_total: float | None = None
) -> dict:
    return database.get_tournament_stats(
        buyin_total
    )


def get_current_bankroll() -> float:
    return database.get_current_bankroll()


def add_mtt_correction(
    date: str,
    amount: float,
    buyin_total: float | None = None
) -> None:
    database.add_mtt_correction(
        date,
        amount,
        buyin_total
    )