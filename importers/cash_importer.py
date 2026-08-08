import os

import config

from database.database import Database
from parsers.cash_parser import parse_cash_hand
from services.session_service import SessionService


HAND_START = b"PokerStars Hand #"
SUMMARY_MARKER = b"*** SUMMARY ***"


class CashImporter:
    def __init__(
        self,
        database: Database,
        folder: str = config.POKERSTARS_FOLDER,
        player_name: str = config.PLAYER_NAME
    ):
        self.database = database
        self.folder = folder
        self.player_name = player_name
        self.session_service = SessionService(database)

    def import_hands(self) -> int:
        if not os.path.isdir(self.folder):
            raise FileNotFoundError(
                f"Dossier PokerStars introuvable : {self.folder}"
            )

        imported_count = 0

        for root, _, files in os.walk(self.folder):
            for filename in files:
                if not filename.lower().endswith(".txt"):
                    continue

                file_path = os.path.join(root, filename)

                imported_count += self._import_file(file_path)

        return imported_count

    def _import_file(self, file_path: str) -> int:
        setting_key = self._get_file_setting_key(file_path)

        saved_position = self.database.get_setting(setting_key)

        try:
            start_position = int(saved_position or 0)
        except ValueError:
            start_position = 0

        try:
            file_size = os.path.getsize(file_path)

            if start_position < 0 or start_position > file_size:
                start_position = 0

            with open(file_path, "rb") as file:
                file.seek(start_position)
                new_content = file.read()

        except OSError as error:
            print(
                f"Impossible de lire le fichier {file_path} : {error}"
            )
            return 0

        if not new_content:
            return 0

        imported_count = 0
        safe_position = start_position

        hand_starts = self._find_hand_starts(new_content)

        for index, relative_start in enumerate(hand_starts):
            if index + 1 < len(hand_starts):
                relative_end = hand_starts[index + 1]
            else:
                relative_end = len(new_content)

            hand_bytes = new_content[relative_start:relative_end]

            summary_position = hand_bytes.find(SUMMARY_MARKER)

            if summary_position == -1:
                break

            summary_end = summary_position + len(SUMMARY_MARKER)

            complete_hand_bytes = hand_bytes[:summary_end]

            hand_text = complete_hand_bytes.decode(
                "utf-8-sig",
                errors="replace"
            )

            parsed_hand = parse_cash_hand(
                hand_text,
                self.player_name
            )

            if parsed_hand is not None:
                hand_id = parsed_hand["hand_id"]

                if not self.database.cash_hand_exists(hand_id):
                    parsed_hand["session_id"] = (
                        self.session_service.assign_session(
                            parsed_hand
                        )
                    )

                    if self.database.insert_cash_hand(parsed_hand):
                        imported_count += 1

            safe_position = (
                start_position
                + relative_start
                + summary_end
            )

        if safe_position > start_position:
            self.database.set_setting(
                setting_key,
                safe_position
            )

        return imported_count

    @staticmethod
    def _find_hand_starts(content: bytes) -> list[int]:
        positions = []
        search_position = 0

        while True:
            position = content.find(
                HAND_START,
                search_position
            )

            if position == -1:
                break

            positions.append(position)

            search_position = position + len(HAND_START)

        return positions

    @staticmethod
    def _get_file_setting_key(file_path: str) -> str:
        normalized_path = os.path.normcase(
            os.path.abspath(file_path)
        )

        return f"cash_file_position::{normalized_path}"