import config

from database.database import create_tables, initialize_bankroll
from ui.interface import start_tracker


def main():

    create_tables()

    initialize_bankroll(config.BANKROLL_START)

    start_tracker()


if __name__ == "__main__":
    main()