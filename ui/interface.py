import tkinter as tk
from datetime import datetime
from tkinter import ttk

import config

from database.database import (
    get_cash_stats,
    get_current_bankroll,
    get_current_session_stats,
    get_tournament_stats
)
from pokerstars_reader import import_cash_hands
from services.bankroll_service import BankrollService


BACKGROUND = "#f1f3f6"
CARD_BACKGROUND = "#ffffff"
TEXT_COLOR = "#1f2937"
SECONDARY_TEXT = "#64748b"
GREEN = "#16803c"
RED = "#c62828"
BLUE = "#2457a7"
BORDER_COLOR = "#d6dbe3"


def format_money(amount: float) -> str:
    return f"{amount:.2f} $".replace(".", ",")


def format_signed_money(amount: float) -> str:
    if amount > 0:
        sign = "+"
    else:
        sign = ""

    return f"{sign}{amount:.2f} $".replace(".", ",")


def format_percentage(value: float) -> str:
    return f"{value:+.2f} %".replace(".", ",")


def format_bb100(value: float) -> str:
    return f"{value:+.2f}".replace(".", ",")


def get_result_color(value: float) -> str:
    if value > 0:
        return GREEN

    if value < 0:
        return RED

    return TEXT_COLOR


def format_session_duration(
    started_at: str | None,
    ended_at: str | None
) -> str:
    if not started_at or not ended_at:
        return "00:00:00"

    start = datetime.fromisoformat(started_at)
    end = datetime.fromisoformat(ended_at)

    total_seconds = max(
        0,
        int((end - start).total_seconds())
    )

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class StatCard(tk.Frame):
    def __init__(
        self,
        parent,
        title: str,
        value: str = "0",
        width: int = 210,
        height: int = 105
    ):
        super().__init__(
            parent,
            bg=CARD_BACKGROUND,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            width=width,
            height=height
        )

        self.pack_propagate(False)

        self.title_label = tk.Label(
            self,
            text=title,
            bg=CARD_BACKGROUND,
            fg=SECONDARY_TEXT,
            font=("Arial", 10)
        )
        self.title_label.pack(
            anchor="w",
            padx=15,
            pady=(14, 4)
        )

        self.value_label = tk.Label(
            self,
            text=value,
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        )
        self.value_label.pack(
            anchor="w",
            padx=15
        )

    def set_value(
        self,
        value: str,
        color: str = TEXT_COLOR
    ) -> None:
        self.value_label.config(
            text=value,
            fg=color
        )


class TrackerApplication:
    def __init__(self):
        self.window = tk.Tk()

        self.window.title("PokerStars Tracker")
        self.window.geometry("820x650")
        self.window.minsize(820, 650)
        self.window.configure(bg=BACKGROUND)

        self.bankroll_service = BankrollService()

        self._configure_styles()
        self._create_header()
        self._create_notebook()
        self._create_dashboard_tab()
        self._create_cash_tab()
        self._create_mtt_tab()
        self._create_bankroll_tab()
        self._create_status_bar()

        self.refresh()

    def _configure_styles(self) -> None:
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Tracker.TNotebook",
            background=BACKGROUND,
            borderwidth=0
        )

        style.configure(
            "Tracker.TNotebook.Tab",
            font=("Arial", 10, "bold"),
            padding=(18, 10),
            background="#dfe4eb",
            foreground=TEXT_COLOR
        )

        style.map(
            "Tracker.TNotebook.Tab",
            background=[
                ("selected", CARD_BACKGROUND),
                ("active", "#e9edf2")
            ],
            foreground=[
                ("selected", BLUE)
            ]
        )

    def _create_header(self) -> None:
        header = tk.Frame(
            self.window,
            bg="#172033",
            height=78
        )
        header.pack(
            fill="x"
        )
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="PokerStars Tracker",
            bg="#172033",
            fg="white",
            font=("Arial", 20, "bold")
        )
        title.pack(
            side="left",
            padx=25,
            pady=18
        )

        self.header_bankroll_label = tk.Label(
            header,
            text="Bankroll : 0,00 $",
            bg="#172033",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.header_bankroll_label.pack(
            side="right",
            padx=25
        )

    def _create_notebook(self) -> None:
        self.notebook = ttk.Notebook(
            self.window,
            style="Tracker.TNotebook"
        )
        self.notebook.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(16, 8)
        )

        self.dashboard_tab = tk.Frame(
            self.notebook,
            bg=BACKGROUND
        )

        self.cash_tab = tk.Frame(
            self.notebook,
            bg=BACKGROUND
        )

        self.mtt_tab = tk.Frame(
            self.notebook,
            bg=BACKGROUND
        )

        self.bankroll_tab = tk.Frame(
            self.notebook,
            bg=BACKGROUND
        )

        self.notebook.add(
            self.dashboard_tab,
            text="Tableau de bord"
        )

        self.notebook.add(
            self.cash_tab,
            text="Cash game"
        )

        self.notebook.add(
            self.mtt_tab,
            text="MTT"
        )

        self.notebook.add(
            self.bankroll_tab,
            text="Bankroll"
        )

    def _create_dashboard_tab(self) -> None:
        title = tk.Label(
            self.dashboard_tab,
            text="Vue d'ensemble",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        )
        title.pack(
            anchor="w",
            padx=10,
            pady=(15, 12)
        )

        row_1 = tk.Frame(
            self.dashboard_tab,
            bg=BACKGROUND
        )
        row_1.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.dashboard_bankroll_card = StatCard(
            row_1,
            "BANKROLL ACTUELLE"
        )
        self.dashboard_bankroll_card.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 7)
        )

        self.dashboard_cash_profit_card = StatCard(
            row_1,
            "PROFIT CASH"
        )
        self.dashboard_cash_profit_card.pack(
            side="left",
            expand=True,
            fill="x",
            padx=7
        )

        self.dashboard_mtt_profit_card = StatCard(
            row_1,
            "PROFIT MTT"
        )
        self.dashboard_mtt_profit_card.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(7, 0)
        )

        row_2 = tk.Frame(
            self.dashboard_tab,
            bg=BACKGROUND
        )
        row_2.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.dashboard_hands_card = StatCard(
            row_2,
            "MAINS CASH"
        )
        self.dashboard_hands_card.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 7)
        )

        self.dashboard_bb100_card = StatCard(
            row_2,
            "BB/100 GLOBAL"
        )
        self.dashboard_bb100_card.pack(
            side="left",
            expand=True,
            fill="x",
            padx=7
        )

        self.dashboard_tournaments_card = StatCard(
            row_2,
            "TOURNOIS"
        )
        self.dashboard_tournaments_card.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(7, 0)
        )

        session_frame = tk.Frame(
            self.dashboard_tab,
            bg=CARD_BACKGROUND,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        session_frame.pack(
            fill="x",
            padx=10,
            pady=(8, 15)
        )

        session_title = tk.Label(
            session_frame,
            text="DERNIÈRE SESSION CASH",
            bg=CARD_BACKGROUND,
            fg=BLUE,
            font=("Arial", 11, "bold")
        )
        session_title.pack(
            anchor="w",
            padx=18,
            pady=(15, 10)
        )

        session_stats = tk.Frame(
            session_frame,
            bg=CARD_BACKGROUND
        )
        session_stats.pack(
            fill="x",
            padx=18,
            pady=(0, 15)
        )

        self.dashboard_session_hands = self._create_inline_stat(
            session_stats,
            "Mains"
        )

        self.dashboard_session_profit = self._create_inline_stat(
            session_stats,
            "Profit"
        )

        self.dashboard_session_bb100 = self._create_inline_stat(
            session_stats,
            "BB/100"
        )

        self.dashboard_session_duration = self._create_inline_stat(
            session_stats,
            "Durée"
        )

    def _create_inline_stat(
        self,
        parent,
        title: str
    ) -> tk.Label:
        frame = tk.Frame(
            parent,
            bg=CARD_BACKGROUND
        )
        frame.pack(
            side="left",
            expand=True,
            fill="x"
        )

        title_label = tk.Label(
            frame,
            text=title,
            bg=CARD_BACKGROUND,
            fg=SECONDARY_TEXT,
            font=("Arial", 9)
        )
        title_label.pack()

        value_label = tk.Label(
            frame,
            text="0",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 13, "bold")
        )
        value_label.pack(
            pady=(3, 0)
        )

        return value_label

    def _create_cash_tab(self) -> None:
        title = tk.Label(
            self.cash_tab,
            text="Statistiques cash game",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        )
        title.pack(
            anchor="w",
            padx=10,
            pady=(15, 12)
        )

        total_frame = tk.LabelFrame(
            self.cash_tab,
            text=" Résultats totaux ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        total_frame.pack(
            fill="x",
            padx=10,
            pady=8
        )

        self.cash_total_hands = self._create_detail_row(
            total_frame,
            "Nombre de mains"
        )

        self.cash_total_profit = self._create_detail_row(
            total_frame,
            "Profit total"
        )

        self.cash_total_profit_bb = self._create_detail_row(
            total_frame,
            "Profit en BB"
        )

        self.cash_total_bb100 = self._create_detail_row(
            total_frame,
            "BB/100"
        )

        session_frame = tk.LabelFrame(
            self.cash_tab,
            text=" Dernière session ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        session_frame.pack(
            fill="x",
            padx=10,
            pady=15
        )

        self.cash_session_hands = self._create_detail_row(
            session_frame,
            "Nombre de mains"
        )

        self.cash_session_profit = self._create_detail_row(
            session_frame,
            "Profit"
        )

        self.cash_session_bb100 = self._create_detail_row(
            session_frame,
            "BB/100"
        )

        self.cash_session_duration = self._create_detail_row(
            session_frame,
            "Durée"
        )

    def _create_detail_row(
        self,
        parent,
        title: str
    ) -> tk.Label:
        row = tk.Frame(
            parent,
            bg=CARD_BACKGROUND
        )
        row.pack(
            fill="x",
            pady=5
        )

        title_label = tk.Label(
            row,
            text=title,
            bg=CARD_BACKGROUND,
            fg=SECONDARY_TEXT,
            font=("Arial", 11)
        )
        title_label.pack(
            side="left"
        )

        value_label = tk.Label(
            row,
            text="0",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold")
        )
        value_label.pack(
            side="right"
        )

        return value_label

    def _create_mtt_tab(self) -> None:
        title = tk.Label(
            self.mtt_tab,
            text="Statistiques MTT",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        )
        title.pack(
            anchor="w",
            padx=10,
            pady=(15, 12)
        )

        stats_frame = tk.LabelFrame(
            self.mtt_tab,
            text=" Résultats totaux ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        stats_frame.pack(
            fill="x",
            padx=10,
            pady=8
        )

        self.mtt_count_label = self._create_detail_row(
            stats_frame,
            "Tournois joués"
        )

        self.mtt_total_cost_label = self._create_detail_row(
            stats_frame,
            "Buy-ins totaux"
        )

        self.mtt_prizes_label = self._create_detail_row(
            stats_frame,
            "Prix remportés"
        )

        self.mtt_profit_label = self._create_detail_row(
            stats_frame,
            "Profit"
        )

        self.mtt_roi_label = self._create_detail_row(
            stats_frame,
            "ROI"
        )

        information = tk.Label(
            self.mtt_tab,
            text=(
                "L'importation automatique des Tournament Summaries "
                "sera ajoutée à la prochaine étape."
            ),
            bg=BACKGROUND,
            fg=SECONDARY_TEXT,
            font=("Arial", 10),
            wraplength=650,
            justify="left"
        )
        information.pack(
            anchor="w",
            padx=15,
            pady=20
        )

    def _create_bankroll_tab(self) -> None:
        title = tk.Label(
            self.bankroll_tab,
            text="Gestion de bankroll",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        )
        title.pack(
            anchor="w",
            padx=10,
            pady=(15, 12)
        )

        recommendation_frame = tk.Frame(
            self.bankroll_tab,
            bg=CARD_BACKGROUND,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        recommendation_frame.pack(
            fill="x",
            padx=10,
            pady=8
        )

        recommendation_title = tk.Label(
            recommendation_frame,
            text="RECOMMANDATION CASH",
            bg=CARD_BACKGROUND,
            fg=BLUE,
            font=("Arial", 11, "bold")
        )
        recommendation_title.pack(
            anchor="w",
            padx=18,
            pady=(16, 8)
        )

        self.bankroll_recommended_limit = tk.Label(
            recommendation_frame,
            text="Limite recommandée : NL2",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        )
        self.bankroll_recommended_limit.pack(
            anchor="w",
            padx=18,
            pady=5
        )

        self.bankroll_message = tk.Label(
            recommendation_frame,
            text="",
            bg=CARD_BACKGROUND,
            fg=SECONDARY_TEXT,
            font=("Arial", 10),
            wraplength=700,
            justify="left"
        )
        self.bankroll_message.pack(
            anchor="w",
            padx=18,
            pady=(3, 16)
        )

        progress_frame = tk.LabelFrame(
            self.bankroll_tab,
            text=" Prochaine limite ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        progress_frame.pack(
            fill="x",
            padx=10,
            pady=12
        )

        self.bankroll_next_limit = self._create_detail_row(
            progress_frame,
            "Prochaine limite"
        )

        self.bankroll_required = self._create_detail_row(
            progress_frame,
            "Bankroll ciblée"
        )

        self.bankroll_missing = self._create_detail_row(
            progress_frame,
            "Montant manquant"
        )

        rules_frame = tk.LabelFrame(
            self.bankroll_tab,
            text=" Règles utilisées ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        rules_frame.pack(
            fill="x",
            padx=10,
            pady=12
        )

        rules_text = (
            f"Limite jouable : {config.CASH_MIN_BUYINS} buy-ins\n"
            f"Shot prudent : {config.CASH_SHOT_BUYINS} buy-ins\n"
            f"Un buy-in cash : {config.CASH_BUYIN_BIG_BLINDS} BB\n\n"
            "Ces valeurs peuvent être modifiées dans config.py."
        )

        rules_label = tk.Label(
            rules_frame,
            text=rules_text,
            bg=CARD_BACKGROUND,
            fg=SECONDARY_TEXT,
            font=("Arial", 10),
            justify="left"
        )
        rules_label.pack(
            anchor="w"
        )

    def _create_status_bar(self) -> None:
        self.status_label = tk.Label(
            self.window,
            text="Initialisation du tracker...",
            bg="#172033",
            fg="white",
            font=("Arial", 9),
            anchor="w",
            padx=15
        )
        self.status_label.pack(
            fill="x",
            side="bottom"
        )

    def refresh(self) -> None:
        try:
            new_hands = import_cash_hands()

            cash_stats = get_cash_stats()
            session_stats = get_current_session_stats()
            tournament_stats = get_tournament_stats()
            bankroll = get_current_bankroll()

            bankroll_plan = self.bankroll_service.get_plan(
                bankroll
            )

            self._update_header(bankroll)
            self._update_dashboard(
                bankroll,
                cash_stats,
                session_stats,
                tournament_stats
            )
            self._update_cash_tab(
                cash_stats,
                session_stats
            )
            self._update_mtt_tab(
                tournament_stats
            )
            self._update_bankroll_tab(
                bankroll_plan
            )

            if new_hands > 0:
                self.status_label.config(
                    text=(
                        f"{new_hands} nouvelle(s) main(s) importée(s)"
                    ),
                    bg=GREEN
                )
            else:
                self.status_label.config(
                    text="Tracker actif — aucune nouvelle main",
                    bg="#172033"
                )

        except Exception as error:
            self.status_label.config(
                text=f"Erreur : {error}",
                bg=RED
            )

            print(
                f"Erreur pendant l'actualisation : {error}"
            )

        self.window.after(
            5000,
            self.refresh
        )

    def _update_header(
        self,
        bankroll: float
    ) -> None:
        self.header_bankroll_label.config(
            text=f"Bankroll : {format_money(bankroll)}"
        )

    def _update_dashboard(
        self,
        bankroll: float,
        cash_stats: dict,
        session_stats: dict,
        tournament_stats: dict
    ) -> None:
        self.dashboard_bankroll_card.set_value(
            format_money(bankroll)
        )

        self.dashboard_cash_profit_card.set_value(
            format_signed_money(cash_stats["profit"]),
            get_result_color(cash_stats["profit"])
        )

        self.dashboard_mtt_profit_card.set_value(
            format_signed_money(tournament_stats["profit"]),
            get_result_color(tournament_stats["profit"])
        )

        self.dashboard_hands_card.set_value(
            f"{cash_stats['hands']:,}".replace(",", " ")
        )

        self.dashboard_bb100_card.set_value(
            format_bb100(cash_stats["bb100"]),
            get_result_color(cash_stats["bb100"])
        )

        self.dashboard_tournaments_card.set_value(
            str(tournament_stats["tournaments"])
        )

        self.dashboard_session_hands.config(
            text=str(session_stats["hands"])
        )

        self.dashboard_session_profit.config(
            text=format_signed_money(
                session_stats["profit"]
            ),
            fg=get_result_color(
                session_stats["profit"]
            )
        )

        self.dashboard_session_bb100.config(
            text=format_bb100(
                session_stats["bb100"]
            ),
            fg=get_result_color(
                session_stats["bb100"]
            )
        )

        duration = format_session_duration(
            session_stats["started_at"],
            session_stats["ended_at"]
        )

        self.dashboard_session_duration.config(
            text=duration
        )

    def _update_cash_tab(
        self,
        cash_stats: dict,
        session_stats: dict
    ) -> None:
        self.cash_total_hands.config(
            text=f"{cash_stats['hands']:,}".replace(",", " ")
        )

        self.cash_total_profit.config(
            text=format_signed_money(
                cash_stats["profit"]
            ),
            fg=get_result_color(
                cash_stats["profit"]
            )
        )

        self.cash_total_profit_bb.config(
            text=f"{cash_stats['profit_bb']:+.2f} BB".replace(
                ".",
                ","
            ),
            fg=get_result_color(
                cash_stats["profit_bb"]
            )
        )

        self.cash_total_bb100.config(
            text=format_bb100(
                cash_stats["bb100"]
            ),
            fg=get_result_color(
                cash_stats["bb100"]
            )
        )

        self.cash_session_hands.config(
            text=str(session_stats["hands"])
        )

        self.cash_session_profit.config(
            text=format_signed_money(
                session_stats["profit"]
            ),
            fg=get_result_color(
                session_stats["profit"]
            )
        )

        self.cash_session_bb100.config(
            text=format_bb100(
                session_stats["bb100"]
            ),
            fg=get_result_color(
                session_stats["bb100"]
            )
        )

        duration = format_session_duration(
            session_stats["started_at"],
            session_stats["ended_at"]
        )

        self.cash_session_duration.config(
            text=duration
        )

    def _update_mtt_tab(
        self,
        tournament_stats: dict
    ) -> None:
        self.mtt_count_label.config(
            text=str(
                tournament_stats["tournaments"]
            )
        )

        self.mtt_total_cost_label.config(
            text=format_money(
                tournament_stats["total_cost"]
            )
        )

        self.mtt_prizes_label.config(
            text=format_money(
                tournament_stats["total_prizes"]
            )
        )

        self.mtt_profit_label.config(
            text=format_signed_money(
                tournament_stats["profit"]
            ),
            fg=get_result_color(
                tournament_stats["profit"]
            )
        )

        self.mtt_roi_label.config(
            text=format_percentage(
                tournament_stats["roi"]
            ),
            fg=get_result_color(
                tournament_stats["roi"]
            )
        )

    def _update_bankroll_tab(
        self,
        plan: dict
    ) -> None:
        recommended_limit = plan["recommended_limit"]

        self.bankroll_recommended_limit.config(
            text=f"Limite recommandée : {recommended_limit}"
        )

        self.bankroll_message.config(
            text=plan["message"]
        )

        next_limit = plan["next_limit"]

        if next_limit is None:
            self.bankroll_next_limit.config(
                text="Aucune"
            )

            self.bankroll_required.config(
                text="—"
            )

            self.bankroll_missing.config(
                text="0,00 $",
                fg=GREEN
            )

            return

        self.bankroll_next_limit.config(
            text=next_limit
        )

        self.bankroll_required.config(
            text=format_money(
                plan["next_required"]
            )
        )

        missing = plan["amount_needed"]

        self.bankroll_missing.config(
            text=format_money(missing),
            fg=GREEN if missing <= 0 else TEXT_COLOR
        )

    def run(self) -> None:
        self.window.mainloop()


def start_tracker() -> None:
    application = TrackerApplication()
    application.run()