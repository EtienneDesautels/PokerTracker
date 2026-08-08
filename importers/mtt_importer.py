import os
from datetime import datetime

import config

from database.database import Database
from parsers.mtt_parser import parse_mtt_summary


class MTTImporter:
    def __init__(
        self,
        database: Database,
        folder: str = config.TOURNAMENT_FOLDER,
        player_name: str = config.PLAYER_NAME,
        tracking_start_date: str = config.TRACKING_START_DATE
    ):
        self.database = database
        self.folder = folder
        self.player_name = player_name
        self.tracking_start_date = datetime.fromisoformat(
            tracking_start_date
        )

    def import_tournaments(self) -> int:
        print(f"Dossier MTT utilisé : {self.folder}")

        if not os.path.isdir(self.folder):
            print("ERREUR : le dossier MTT est introuvable.")

            raise FileNotFoundError(
                "Dossier Tournament Summary introuvable : "
                f"{self.folder}"
            )

        imported_count = 0
        txt_files_found = 0

        for root, _, files in os.walk(self.folder):
            for filename in files:
                if not filename.lower().endswith(".txt"):
                    continue

                txt_files_found += 1

                file_path = os.path.join(
                    root,
                    filename
                )

                imported_count += self._import_file(
                    file_path
                )

        print(
            f"Fichiers MTT .txt trouvés : {txt_files_found}"
        )

        print(
            f"Nouveaux tournois importés : {imported_count}"
        )

        return imported_count

    def _import_file(
        self,
        file_path: str
    ) -> int:
        try:
            with open(
                file_path,
                "r",
                encoding="utf-8-sig",
                errors="replace"
            ) as file:
                summary_text = file.read()

        except OSError as error:
            print(
                f"Impossible de lire {file_path} : {error}"
            )
            return 0

        parsed_tournament = parse_mtt_summary(
            summary_text,
            self.player_name
        )

        if parsed_tournament is None:
            print(
                "Résumé non reconnu ou tournoi incomplet : "
                f"{os.path.basename(file_path)}"
            )
            return 0

        print(
            "Tournoi reconnu : "
            f"#{parsed_tournament['tournament_id']} | "
            f"place {parsed_tournament['place']} | "
            f"prix {parsed_tournament['prize']:.2f} $"
        )

        tournament_date = datetime.fromisoformat(
            parsed_tournament["date"]
        )

        if tournament_date < self.tracking_start_date:
            print(
                "Tournoi ignoré, car il précède "
                f"TRACKING_START_DATE : {file_path}"
            )
            return 0

        tournament_id = parsed_tournament["tournament_id"]

        if self.database.tournament_exists(
            tournament_id
        ):
            print(
                f"Tournoi déjà présent : #{tournament_id}"
            )
            return 0

        if self.database.insert_tournament(
            parsed_tournament
        ):
            print(
                f"Tournoi ajouté : #{tournament_id}"
            )
            return 1

        return 0