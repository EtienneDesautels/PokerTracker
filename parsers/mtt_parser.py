import re
from datetime import datetime


def parse_number(number_text: str) -> float:
    """
    Transforme les montants PokerStars français.

    Exemples :
    16,46 -> 16.46
    0.98  -> 0.98
    """

    cleaned_number = (
        number_text
        .replace("\xa0", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    return float(cleaned_number)


def parse_mtt_summary(
    summary_text: str,
    player_name: str
) -> dict | None:
    """
    Analyse un Tournament Summary PokerStars en français.

    Retourne None si le résumé est incomplet ou invalide.
    """

    tournament_match = re.search(
        r"PokerStars Tournoi #(\d+),\s*(.+)",
        summary_text
    )

    buyin_match = re.search(
        r"Buy-in\s*:\s*"
        r"\$([0-9]+(?:[.,][0-9]+)?)/"
        r"\$([0-9]+(?:[.,][0-9]+)?)"
        r"\s+USD",
        summary_text
    )

    players_match = re.search(
        r"(\d+)\s+joueurs",
        summary_text
    )

    date_match = re.search(
        r"Tournoi commencé\s+"
        r"(\d{2}/\d{2}/\d{4}\s+"
        r"\d{2}:\d{2}:\d{2})\s+ET",
        summary_text
    )

    place_match = re.search(
        r"Vous avez terminé à la\s+"
        r"(\d+)(?:e|er)\s+place",
        summary_text
    )

    required_matches = (
        tournament_match,
        buyin_match,
        players_match,
        date_match,
        place_match
    )

    if not all(required_matches):
        return None

    tournament_id = tournament_match.group(1)
    tournament_type = tournament_match.group(2).strip()

    buyin = parse_number(
        buyin_match.group(1)
    )

    rake = parse_number(
        buyin_match.group(2)
    )

    players = int(
        players_match.group(1)
    )

    place = int(
        place_match.group(1)
    )

    parsed_date = datetime.strptime(
        date_match.group(1),
        "%d/%m/%Y %H:%M:%S"
    )

    tournament_date = parsed_date.isoformat(
        sep=" ",
        timespec="seconds"
    )

    escaped_player_name = re.escape(
        player_name
    )

    player_line_match = re.search(
        rf"^\s*(\d+):\s*"
        rf"{escaped_player_name}"
        rf"(?:\s+\[\d+\])?"
        rf"\s+\([^)]*\),"
        rf"\s*(?:\$([0-9]+(?:[.,][0-9]+)?))?",
        summary_text,
        flags=re.MULTILINE
    )

    prize = 0.0

    if player_line_match:
        prize_text = player_line_match.group(2)

        if prize_text:
            prize = parse_number(
                prize_text
            )

    total_cost = buyin + rake
    profit = prize - total_cost

    return {
        "tournament_id": tournament_id,
        "date": tournament_date,
        "tournament_type": tournament_type,
        "buyin": round(buyin, 4),
        "rake": round(rake, 4),
        "prize": round(prize, 4),
        "profit": round(profit, 4),
        "place": place,
        "players": players
    }