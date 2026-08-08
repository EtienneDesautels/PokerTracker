import config


class BankrollService:
    def __init__(
        self,
        stakes: dict[str, float] | None = None,
        minimum_buyins: int = config.CASH_MIN_BUYINS,
        shot_buyins: int = config.CASH_SHOT_BUYINS,
        buyin_big_blinds: int = config.CASH_BUYIN_BIG_BLINDS
    ):
        self.stakes = stakes or config.CASH_STAKES
        self.minimum_buyins = minimum_buyins
        self.shot_buyins = shot_buyins
        self.buyin_big_blinds = buyin_big_blinds

    def get_plan(self, bankroll: float) -> dict:
        ordered_stakes = sorted(
            self.stakes.items(),
            key=lambda item: item[1]
        )

        playable_limit = None
        playable_bb = None

        for limit_name, big_blind in ordered_stakes:
            required_bankroll = self.get_required_bankroll(
                big_blind,
                self.minimum_buyins
            )

            if bankroll >= required_bankroll:
                playable_limit = limit_name
                playable_bb = big_blind

        if playable_limit is None:
            first_limit_name, first_big_blind = ordered_stakes[0]

            required = self.get_required_bankroll(
                first_big_blind,
                self.minimum_buyins
            )

            return {
                "status": "insufficient",
                "recommended_limit": first_limit_name,
                "recommended_bb": first_big_blind,
                "recommended_buyin": self.get_buyin(first_big_blind),
                "next_limit": first_limit_name,
                "next_required": required,
                "amount_needed": max(0.0, required - bankroll),
                "message": (
                    f"Bankroll sous le seuil de "
                    f"{self.minimum_buyins} buy-ins pour {first_limit_name}."
                )
            }

        playable_index = next(
            index
            for index, stake in enumerate(ordered_stakes)
            if stake[0] == playable_limit
        )

        next_index = playable_index + 1

        if next_index >= len(ordered_stakes):
            return {
                "status": "maximum",
                "recommended_limit": playable_limit,
                "recommended_bb": playable_bb,
                "recommended_buyin": self.get_buyin(playable_bb),
                "next_limit": None,
                "next_required": None,
                "amount_needed": 0.0,
                "message": (
                    f"Bankroll suffisante pour la plus haute "
                    f"limite configurée : {playable_limit}."
                )
            }

        next_limit, next_big_blind = ordered_stakes[next_index]

        shot_required = self.get_required_bankroll(
            next_big_blind,
            self.shot_buyins
        )

        amount_needed = max(
            0.0,
            shot_required - bankroll
        )

        if amount_needed == 0:
            status = "shot_ready"
            message = (
                f"Ta bankroll permet un shot prudent en {next_limit}."
            )
        else:
            status = "building"
            message = (
                f"Continue en {playable_limit}. "
                f"Il manque {amount_needed:.2f} $ "
                f"pour atteindre {self.shot_buyins} buy-ins "
                f"de {next_limit}."
            )

        return {
            "status": status,
            "recommended_limit": playable_limit,
            "recommended_bb": playable_bb,
            "recommended_buyin": self.get_buyin(playable_bb),
            "next_limit": next_limit,
            "next_required": shot_required,
            "amount_needed": amount_needed,
            "message": message
        }

    def get_buyin(self, big_blind: float) -> float:
        return big_blind * self.buyin_big_blinds

    def get_required_bankroll(
        self,
        big_blind: float,
        buyins: int
    ) -> float:
        return self.get_buyin(big_blind) * buyins

    def get_stakes_table(self, bankroll: float) -> list[dict]:
        table = []

        for limit_name, big_blind in sorted(
            self.stakes.items(),
            key=lambda item: item[1]
        ):
            buyin = self.get_buyin(big_blind)

            minimum_required = self.get_required_bankroll(
                big_blind,
                self.minimum_buyins
            )

            shot_required = self.get_required_bankroll(
                big_blind,
                self.shot_buyins
            )

            table.append({
                "limit": limit_name,
                "big_blind": big_blind,
                "buyin": buyin,
                "minimum_required": minimum_required,
                "shot_required": shot_required,
                "playable": bankroll >= minimum_required,
                "shot_ready": bankroll >= shot_required
            })

        return table