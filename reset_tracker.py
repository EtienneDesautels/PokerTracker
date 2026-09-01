from database.database import database
import config


def reset_tracker():
    with database.connect() as connection:
        cursor = connection.cursor()

        # Données cash
        cursor.execute("DELETE FROM cash_hands")
        cursor.execute("DELETE FROM cash_sessions")

        # Données MTT
        cursor.execute("DELETE FROM tournaments")
        cursor.execute("DELETE FROM mtt_corrections")

        # Positions de lecture des fichiers PokerStars
        cursor.execute("""
            DELETE FROM settings
            WHERE key LIKE 'cash_file_position::%'
        """)

        cursor.execute("""
            DELETE FROM settings
            WHERE key LIKE 'mtt_file_signature::%'
        """)

        # Remet la bankroll de départ selon config.py
        cursor.execute("""
            INSERT INTO settings(key, value)
            VALUES('starting_bankroll', ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
        """, (
            str(config.BANKROLL_START),
        ))

        # Remet les compteurs autoincrement à zéro
        cursor.execute("""
            DELETE FROM sqlite_sequence
            WHERE name IN (
                'cash_sessions',
                'mtt_corrections'
            )
        """)

    print("================================")
    print("Tracker réinitialisé.")
    print("================================")
    print(f"Bankroll de départ : {config.BANKROLL_START:.2f} $")
    print("Mains cash : 0")
    print("Sessions cash : 0")
    print("Tournois MTT : 0")
    print("Corrections MTT : 0")
    print("Positions d'import : réinitialisées")


if __name__ == "__main__":
    confirmation = input(
        "\nToutes les données du tracker seront supprimées.\n"
        "Tape OUI pour continuer : "
    )

    if confirmation.strip().upper() == "OUI":
        reset_tracker()
    else:
        print("Reset annulé.")