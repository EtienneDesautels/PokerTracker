from datetime import datetime, timedelta

from database.database import Database


SESSION_TIMEOUT = timedelta(minutes=20)


class SessionService:
    def __init__(self, database: Database):
        self.database = database

    def assign_session(self, hand: dict) -> int:
        hand_date = self._parse_date(hand["date"])

        last_hand = self.database.get_last_cash_hand()

        if last_hand is None:
            return self.database.create_cash_session(
                hand["date"]
            )

        last_hand_date = self._parse_date(
            last_hand["date"]
        )

        time_difference = hand_date - last_hand_date

        should_create_new_session = (
            last_hand["session_id"] is None
            or time_difference >= SESSION_TIMEOUT
            or time_difference.total_seconds() < 0
        )

        if should_create_new_session:
            return self.database.create_cash_session(
                hand["date"]
            )

        session_id = int(last_hand["session_id"])

        self.database.update_cash_session_end(
            session_id,
            hand["date"]
        )

        return session_id

    @staticmethod
    def _parse_date(date_text: str | None) -> datetime:
        if not isinstance(date_text, str) or not date_text.strip():
            raise ValueError(
                "Date absente ou invalide pour la session"
            )

        return datetime.fromisoformat(date_text)