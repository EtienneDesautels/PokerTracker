from database.database import database
from importers.cash_importer import CashImporter
from importers.mtt_importer import MTTImporter


cash_importer = CashImporter(database)
mtt_importer = MTTImporter(database)


def import_all_results() -> dict:
    new_cash_hands = cash_importer.import_hands()
    new_tournaments = mtt_importer.import_tournaments()

    return {
        "cash_hands": new_cash_hands,
        "tournaments": new_tournaments,
        "total": new_cash_hands + new_tournaments
    }


def import_cash_hands() -> int:
    """
    Nom conservé pour que l’interface actuelle fonctionne.
    Cette fonction importe le cash et les MTT.
    """

    results = import_all_results()

    print(
        "Import terminé — "
        f"cash : {results['cash_hands']}, "
        f"MTT : {results['tournaments']}"
    )

    return results["total"]