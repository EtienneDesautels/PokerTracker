import re
from datetime import datetime


MONEY_PATTERN = r"\$([0-9]+(?:\.[0-9]+)?)"


def parse_cash_hand(hand_text, player_name):
    """
    Analyse une main PokerStars cash game.

    Retourne un dictionnaire contenant :
    - hand_id
    - date
    - limite
    - sb
    - bb
    - profit
    - profit_bb

    Retourne None si la main ne peut pas être analysée.
    """

    hand_id_match = re.search(
        r"PokerStars Hand #(\d+)",
        hand_text
    )

    blinds_match = re.search(
        r"Hold'em No Limit \(\$([0-9.]+)/\$([0-9.]+) USD\)",
        hand_text
    )

    date_match = re.search(
        r"- (\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) ET",
        hand_text
    )

    if not hand_id_match or not blinds_match:
        return None

    hand_id = hand_id_match.group(1)

    sb = float(blinds_match.group(1))
    bb = float(blinds_match.group(2))

    limite = f"NL{round(bb * 100)}"

    hand_date = None

    if date_match:
        parsed_date = datetime.strptime(
            date_match.group(1),
            "%Y/%m/%d %H:%M:%S"
        )

        hand_date = parsed_date.isoformat(
            sep=" ",
            timespec="seconds"
        )

    invested = 0.0
    collected = 0.0
    returned = 0.0

    # Montant déjà investi par le joueur pendant la rue actuelle.
    street_investment = 0.0

    escaped_player = re.escape(player_name)

    for original_line in hand_text.splitlines():
        line = original_line.strip()

        # Nouvelle rue : les mises repartent à zéro.
        if line.startswith("*** FLOP"):
            street_investment = 0.0
            continue

        if line.startswith("*** TURN"):
            street_investment = 0.0
            continue

        if line.startswith("*** RIVER"):
            street_investment = 0.0
            continue

        if not line.startswith(f"{player_name}:"):
            # Exemples :
            # Uncalled bet ($0.18) returned to Dérouxo
            # Dérouxo collected $0.35 from pot

            returned_match = re.search(
                rf"Uncalled bet \({MONEY_PATTERN}\) "
                rf"returned to {escaped_player}",
                line
            )

            if returned_match:
                returned += float(returned_match.group(1))

            collected_match = re.search(
                rf"^{escaped_player} collected "
                rf"{MONEY_PATTERN} from pot",
                line
            )

            if collected_match:
                collected += float(collected_match.group(1))

            continue

        # Petite blind, grosse blind ou ante.
        post_match = re.search(
            rf"^{escaped_player}: posts "
            rf"(?:small blind|big blind|the ante) "
            rf"{MONEY_PATTERN}",
            line
        )

        if post_match:
            amount = float(post_match.group(1))
            invested += amount
            street_investment += amount
            continue

        # Call.
        call_match = re.search(
            rf"^{escaped_player}: calls {MONEY_PATTERN}",
            line
        )

        if call_match:
            amount = float(call_match.group(1))
            invested += amount
            street_investment += amount
            continue

        # Bet.
        bet_match = re.search(
            rf"^{escaped_player}: bets {MONEY_PATTERN}",
            line
        )

        if bet_match:
            amount = float(bet_match.group(1))
            invested += amount
            street_investment += amount
            continue

        # Raise : PokerStars indique le montant total de la mise.
        # Exemple : raises $0.04 to $0.10
        raise_match = re.search(
            rf"^{escaped_player}: raises "
            rf"{MONEY_PATTERN} to {MONEY_PATTERN}",
            line
        )

        if raise_match:
            total_raise = float(raise_match.group(2))

            additional_amount = max(
                0.0,
                total_raise - street_investment
            )

            invested += additional_amount
            street_investment = total_raise

    profit = collected + returned - invested

    profit_bb = profit / bb if bb > 0 else 0.0

    return {
        "hand_id": hand_id,
        "date": hand_date,
        "limite": limite,
        "sb": round(sb, 4),
        "bb": round(bb, 4),
        "profit": round(profit, 4),
        "profit_bb": round(profit_bb, 4)
    }
