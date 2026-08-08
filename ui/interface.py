import tkinter as tk

from datetime import datetime

from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog

import config

from database.database import (
    get_cash_limits,
    get_cash_stats,
    get_current_bankroll,
    get_current_session_stats,
    get_mtt_buyins,
    get_tournament_stats,
    add_mtt_correction
)

from pokerstars_reader import import_cash_hands

from services.bankroll_service import (
    BankrollService
)


# =========================================================
# COULEURS
# =========================================================

BACKGROUND = "#f1f3f6"

CARD_BACKGROUND = "#ffffff"

TEXT_COLOR = "#1f2937"

SECONDARY_TEXT = "#64748b"

GREEN = "#16803c"

RED = "#c62828"

BLUE = "#2457a7"

BORDER_COLOR = "#d6dbe3"

HEADER_COLOR = "#172033"


# =========================================================
# FORMATAGE
# =========================================================

def format_money(
    amount: float
) -> str:

    return (
        f"{amount:.2f} $"
        .replace(".", ",")
    )


def format_signed_money(
    amount: float
) -> str:

    sign = ""

    if amount > 0:
        sign = "+"

    return (
        f"{sign}{amount:.2f} $"
        .replace(".", ",")
    )


def format_percentage(
    value: float
) -> str:

    return (
        f"{value:+.2f} %"
        .replace(".", ",")
    )


def format_bb100(
    value: float
) -> str:

    return (
        f"{value:+.2f}"
        .replace(".", ",")
    )


def format_number(
    value: int
) -> str:

    return (
        f"{value:,}"
        .replace(",", " ")
    )


def get_result_color(
    value: float
) -> str:

    if value > 0:
        return GREEN

    if value < 0:
        return RED

    return TEXT_COLOR


def parse_money(
    text: str
) -> float:

    cleaned_text = (
        text.strip()
        .replace("$", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    if not cleaned_text:
        raise ValueError(
            "Le montant est vide."
        )

    return round(
        float(cleaned_text),
        2
    )


def format_session_duration(
    started_at: str | None,
    ended_at: str | None
) -> str:

    if not started_at or not ended_at:
        return "00:00:00"

    start = datetime.fromisoformat(
        started_at
    )

    end = datetime.fromisoformat(
        ended_at
    )

    total_seconds = max(
        0,
        int(
            (
                end
                - start
            ).total_seconds()
        )
    )

    hours, remainder = divmod(
        total_seconds,
        3600
    )

    minutes, seconds = divmod(
        remainder,
        60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


# =========================================================
# CARTE STATISTIQUE
# =========================================================

class StatCard(
    tk.Frame
):

    def __init__(
        self,
        parent,
        title: str,
        value: str = "0"
    ):

        super().__init__(
            parent,
            bg=CARD_BACKGROUND,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            height=105
        )

        self.pack_propagate(
            False
        )

        title_label = tk.Label(
            self,
            text=title,
            bg=CARD_BACKGROUND,
            fg=SECONDARY_TEXT,
            font=(
                "Arial",
                10
            )
        )

        title_label.pack(
            anchor="w",
            padx=15,
            pady=(14, 4)
        )

        self.value_label = tk.Label(
            self,
            text=value,
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                18,
                "bold"
            )
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


# =========================================================
# APPLICATION
# =========================================================

class TrackerApplication:

    def __init__(
        self
    ):

        self.window = tk.Tk()

        self.window.title(
            "PokerStars Tracker"
        )

        self.window.geometry(
            "900x720"
        )

        self.window.minsize(
            900,
            720
        )

        self.window.configure(
            bg=BACKGROUND
        )

        self.bankroll_service = (
            BankrollService()
        )

        # Valeurs de filtre
        self.cash_filter_value = (
            tk.StringVar(
                value="Toutes les limites"
            )
        )

        self.mtt_filter_value = (
            tk.StringVar(
                value="Tous les buy-ins"
            )
        )

        self._configure_styles()

        self._create_header()

        self._create_notebook()

        self._create_dashboard_tab()

        self._create_cash_tab()

        self._create_mtt_tab()

        self._create_bankroll_tab()

        self._create_status_bar()

        self.refresh()

    # =====================================================
    # STYLE
    # =====================================================

    def _configure_styles(
        self
    ) -> None:

        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )

        except tk.TclError:
            pass

        style.configure(
            "Tracker.TNotebook",
            background=BACKGROUND,
            borderwidth=0
        )

        style.configure(
            "Tracker.TNotebook.Tab",
            font=(
                "Arial",
                10,
                "bold"
            ),
            padding=(
                18,
                10
            )
        )

    # =====================================================
    # HEADER
    # =====================================================

    def _create_header(
        self
    ) -> None:

        header = tk.Frame(
            self.window,
            bg=HEADER_COLOR,
            height=78
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        title = tk.Label(
            header,
            text="PokerStars Tracker",
            bg=HEADER_COLOR,
            fg="white",
            font=(
                "Arial",
                20,
                "bold"
            )
        )

        title.pack(
            side="left",
            padx=25,
            pady=18
        )

        self.header_bankroll_label = (
            tk.Label(
                header,
                text="Bankroll : 0,00 $",
                bg=HEADER_COLOR,
                fg="white",
                font=(
                    "Arial",
                    14,
                    "bold"
                )
            )
        )

        self.header_bankroll_label.pack(
            side="right",
            padx=25
        )

    # =====================================================
    # ONGLETS
    # =====================================================

    def _create_notebook(
        self
    ) -> None:

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

    # =====================================================
    # DASHBOARD
    # =====================================================

    def _create_dashboard_tab(
        self
    ) -> None:

        title = tk.Label(
            self.dashboard_tab,
            text="Vue d'ensemble",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                18,
                "bold"
            )
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

        self.dashboard_bankroll = (
            StatCard(
                row_1,
                "BANKROLL"
            )
        )

        self.dashboard_cash_profit = (
            StatCard(
                row_1,
                "PROFIT CASH"
            )
        )

        self.dashboard_mtt_profit = (
            StatCard(
                row_1,
                "PROFIT MTT"
            )
        )

        self.dashboard_bankroll.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 7)
        )

        self.dashboard_cash_profit.pack(
            side="left",
            expand=True,
            fill="x",
            padx=7
        )

        self.dashboard_mtt_profit.pack(
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

        self.dashboard_hands = (
            StatCard(
                row_2,
                "MAINS CASH"
            )
        )

        self.dashboard_bb100 = (
            StatCard(
                row_2,
                "BB/100"
            )
        )

        self.dashboard_tournaments = (
            StatCard(
                row_2,
                "TOURNOIS"
            )
        )

        self.dashboard_hands.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 7)
        )

        self.dashboard_bb100.pack(
            side="left",
            expand=True,
            fill="x",
            padx=7
        )

        self.dashboard_tournaments.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(7, 0)
        )

    # =====================================================
    # CASH TAB
    # =====================================================

    def _create_cash_tab(
        self
    ) -> None:

        top = tk.Frame(
            self.cash_tab,
            bg=BACKGROUND
        )

        top.pack(
            fill="x",
            padx=10,
            pady=(15, 8)
        )

        title = tk.Label(
            top,
            text="Statistiques cash game",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                18,
                "bold"
            )
        )

        title.pack(
            side="left"
        )

        filter_frame = tk.Frame(
            top,
            bg=BACKGROUND
        )

        filter_frame.pack(
            side="right"
        )

        tk.Label(
            filter_frame,
            text="Limite :",
            bg=BACKGROUND,
            fg=SECONDARY_TEXT,
            font=(
                "Arial",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(0, 7)
        )

        self.cash_filter = (
            ttk.Combobox(
                filter_frame,
                textvariable=(
                    self.cash_filter_value
                ),
                state="readonly",
                width=20
            )
        )

        self.cash_filter.pack(
            side="left"
        )

        self.cash_filter.bind(
            "<<ComboboxSelected>>",
            self._cash_filter_changed
        )

        stats_frame = tk.LabelFrame(
            self.cash_tab,
            text=" Résultats ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                11,
                "bold"
            ),
            padx=20,
            pady=15
        )

        stats_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.cash_hands = (
            self._create_detail_row(
                stats_frame,
                "Nombre de mains"
            )
        )

        self.cash_profit = (
            self._create_detail_row(
                stats_frame,
                "Profit"
            )
        )

        self.cash_profit_bb = (
            self._create_detail_row(
                stats_frame,
                "Profit en BB"
            )
        )

        self.cash_bb100 = (
            self._create_detail_row(
                stats_frame,
                "BB/100"
            )
        )

        session_frame = tk.LabelFrame(
            self.cash_tab,
            text=" Dernière session ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                11,
                "bold"
            ),
            padx=20,
            pady=15
        )

        session_frame.pack(
            fill="x",
            padx=10,
            pady=15
        )

        self.session_hands = (
            self._create_detail_row(
                session_frame,
                "Mains"
            )
        )

        self.session_profit = (
            self._create_detail_row(
                session_frame,
                "Profit"
            )
        )

        self.session_bb100 = (
            self._create_detail_row(
                session_frame,
                "BB/100"
            )
        )

        self.session_duration = (
            self._create_detail_row(
                session_frame,
                "Durée"
            )
        )

    # =====================================================
    # MTT TAB
    # =====================================================

    def _create_mtt_tab(
        self
    ) -> None:

        top = tk.Frame(
            self.mtt_tab,
            bg=BACKGROUND
        )

        top.pack(
            fill="x",
            padx=10,
            pady=(15, 8)
        )

        title = tk.Label(
            top,
            text="Statistiques MTT",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                18,
                "bold"
            )
        )

        title.pack(
            side="left"
        )

        filter_frame = tk.Frame(
            top,
            bg=BACKGROUND
        )

        filter_frame.pack(
            side="right"
        )

        tk.Label(
            filter_frame,
            text="Buy-in :",
            bg=BACKGROUND,
            fg=SECONDARY_TEXT,
            font=(
                "Arial",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(0, 7)
        )

        self.mtt_filter = (
            ttk.Combobox(
                filter_frame,
                textvariable=(
                    self.mtt_filter_value
                ),
                state="readonly",
                width=20
            )
        )

        self.mtt_filter.pack(
            side="left"
        )

        self.mtt_filter.bind(
            "<<ComboboxSelected>>",
            self._mtt_filter_changed
        )

        stats_frame = tk.LabelFrame(
            self.mtt_tab,
            text=" Résultats ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                11,
                "bold"
            ),
            padx=20,
            pady=15
        )

        stats_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.mtt_count = (
            self._create_detail_row(
                stats_frame,
                "Tournois"
            )
        )

        self.mtt_cost = (
            self._create_detail_row(
                stats_frame,
                "Buy-ins totaux"
            )
        )

        self.mtt_average_buyin = (
            self._create_detail_row(
                stats_frame,
                "ABI"
            )
        )

        self.mtt_imported_prizes = (
            self._create_detail_row(
                stats_frame,
                "Prix importés"
            )
        )

        self.mtt_corrections = (
            self._create_detail_row(
                stats_frame,
                "Corrections"
            )
        )

        self.mtt_profit = (
            self._create_detail_row(
                stats_frame,
                "Profit"
            )
        )

        self.mtt_roi = (
            self._create_detail_row(
                stats_frame,
                "ROI"
            )
        )

        self.mtt_itm = (
            self._create_detail_row(
                stats_frame,
                "ITM"
            )
        )

        correction_button = tk.Button(
            self.mtt_tab,
            text="Ajouter une correction",
            command=(
                self._add_mtt_correction
            ),
            bg=BLUE,
            fg="white",
            activebackground="#1d478c",
            activeforeground="white",
            relief="flat",
            font=(
                "Arial",
                10,
                "bold"
            ),
            padx=16,
            pady=8
        )

        correction_button.pack(
            anchor="w",
            padx=15,
            pady=15
        )

    # =====================================================
    # BANKROLL TAB
    # =====================================================

    def _create_bankroll_tab(
        self
    ) -> None:

        title = tk.Label(
            self.bankroll_tab,
            text="Gestion de bankroll",
            bg=BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                18,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            padx=10,
            pady=(15, 12)
        )

        frame = tk.LabelFrame(
            self.bankroll_tab,
            text=" Recommandation cash ",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            padx=20,
            pady=15
        )

        frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.bankroll_limit = (
            self._create_detail_row(
                frame,
                "Limite recommandée"
            )
        )

        self.bankroll_next = (
            self._create_detail_row(
                frame,
                "Prochaine limite"
            )
        )

        self.bankroll_target = (
            self._create_detail_row(
                frame,
                "Bankroll ciblée"
            )
        )

        self.bankroll_missing = (
            self._create_detail_row(
                frame,
                "Montant manquant"
            )
        )

    # =====================================================
    # ROW
    # =====================================================

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

        tk.Label(
            row,
            text=title,
            bg=CARD_BACKGROUND,
            fg=SECONDARY_TEXT,
            font=(
                "Arial",
                11
            )
        ).pack(
            side="left"
        )

        value = tk.Label(
            row,
            text="0",
            bg=CARD_BACKGROUND,
            fg=TEXT_COLOR,
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        value.pack(
            side="right"
        )

        return value

    # =====================================================
    # STATUS
    # =====================================================

    def _create_status_bar(
        self
    ) -> None:

        self.status_label = tk.Label(
            self.window,
            text="Initialisation...",
            bg=HEADER_COLOR,
            fg="white",
            anchor="w",
            padx=15
        )

        self.status_label.pack(
            fill="x",
            side="bottom"
        )

    # =====================================================
    # FILTRES
    # =====================================================

    def _refresh_filter_options(
        self
    ) -> None:

        current_cash = (
            self.cash_filter_value.get()
        )

        limits = (
            get_cash_limits()
        )

        cash_values = [
            "Toutes les limites"
        ] + limits

        self.cash_filter[
            "values"
        ] = cash_values

        if current_cash not in cash_values:
            self.cash_filter_value.set(
                "Toutes les limites"
            )

        current_mtt = (
            self.mtt_filter_value.get()
        )

        buyins = (
            get_mtt_buyins()
        )

        mtt_values = [
            "Tous les buy-ins"
        ]

        for buyin in buyins:
            mtt_values.append(
                format_money(
                    buyin
                )
            )

        self.mtt_filter[
            "values"
        ] = mtt_values

        if current_mtt not in mtt_values:
            self.mtt_filter_value.set(
                "Tous les buy-ins"
            )

    def _get_selected_cash_limit(
        self
    ) -> str | None:

        value = (
            self.cash_filter_value.get()
        )

        if value == "Toutes les limites":
            return None

        return value

    def _get_selected_mtt_buyin(
        self
    ) -> float | None:

        value = (
            self.mtt_filter_value.get()
        )

        if value == "Tous les buy-ins":
            return None

        cleaned = (
            value
            .replace("$", "")
            .replace(" ", "")
            .replace(",", ".")
        )

        return float(
            cleaned
        )

    def _cash_filter_changed(
        self,
        event=None
    ) -> None:

        self.refresh_data_only()

    def _mtt_filter_changed(
        self,
        event=None
    ) -> None:

        self.refresh_data_only()

    # =====================================================
    # CORRECTION MTT
    # =====================================================

    def _add_mtt_correction(
        self
    ) -> None:

        selected_buyin = (
            self._get_selected_mtt_buyin()
        )

        if selected_buyin is None:
            explanation = (
                "\n\nLa correction sera globale "
                "et ne sera pas associée à un buy-in."
            )

        else:
            explanation = (
                "\n\nLa correction sera associée au buy-in "
                f"{format_money(selected_buyin)}."
            )

        answer = simpledialog.askstring(
            "Correction MTT",
            (
                "Montant de la correction :"
                "\n"
                "Exemple : 12,45"
                "\n"
                "ou -3,00"
                f"{explanation}"
            ),
            parent=self.window
        )

        if answer is None:
            return

        try:
            amount = parse_money(
                answer
            )

        except ValueError:

            messagebox.showerror(
                "Erreur",
                "Montant invalide.",
                parent=self.window
            )

            return

        if amount == 0:
            return

        date = datetime.now().isoformat(
            sep=" ",
            timespec="seconds"
        )

        add_mtt_correction(
            date,
            amount,
            selected_buyin
        )

        self.refresh_data_only()

    # =====================================================
    # REFRESH PRINCIPAL
    # =====================================================

    def refresh(
        self
    ) -> None:

        try:

            new_results = (
                import_cash_hands()
            )

            self._refresh_filter_options()

            self.refresh_data_only()

            if new_results > 0:
                self.status_label.config(
                    text=(
                        f"{new_results} nouveau(x) "
                        "résultat(s) importé(s)"
                    ),
                    bg=GREEN
                )

            else:
                self.status_label.config(
                    text=(
                        "Tracker actif — "
                        "aucun nouveau résultat"
                    ),
                    bg=HEADER_COLOR
                )

        except Exception as error:

            self.status_label.config(
                text=f"Erreur : {error}",
                bg=RED
            )

            print(
                "Erreur :",
                error
            )

        self.window.after(
            5000,
            self.refresh
        )

    # =====================================================
    # REFRESH DONNÉES
    # =====================================================

    def refresh_data_only(
        self
    ) -> None:

        cash_limit = (
            self._get_selected_cash_limit()
        )

        mtt_buyin = (
            self._get_selected_mtt_buyin()
        )

        global_cash = (
            get_cash_stats()
        )

        global_mtt = (
            get_tournament_stats()
        )

        cash_stats = (
            get_cash_stats(
                cash_limit
            )
        )

        session_stats = (
            get_current_session_stats(
                cash_limit
            )
        )

        mtt_stats = (
            get_tournament_stats(
                mtt_buyin
            )
        )

        bankroll = (
            get_current_bankroll()
        )

        plan = (
            self.bankroll_service.get_plan(
                bankroll
            )
        )

        # HEADER

        self.header_bankroll_label.config(
            text=(
                "Bankroll : "
                f"{format_money(bankroll)}"
            )
        )

        # DASHBOARD = toujours GLOBAL

        self.dashboard_bankroll.set_value(
            format_money(
                bankroll
            )
        )

        self.dashboard_cash_profit.set_value(
            format_signed_money(
                global_cash["profit"]
            ),
            get_result_color(
                global_cash["profit"]
            )
        )

        self.dashboard_mtt_profit.set_value(
            format_signed_money(
                global_mtt["profit"]
            ),
            get_result_color(
                global_mtt["profit"]
            )
        )

        self.dashboard_hands.set_value(
            format_number(
                global_cash["hands"]
            )
        )

        self.dashboard_bb100.set_value(
            format_bb100(
                global_cash["bb100"]
            ),
            get_result_color(
                global_cash["bb100"]
            )
        )

        self.dashboard_tournaments.set_value(
            str(
                global_mtt["tournaments"]
            )
        )

        # CASH FILTRÉ

        self.cash_hands.config(
            text=format_number(
                cash_stats["hands"]
            )
        )

        self.cash_profit.config(
            text=format_signed_money(
                cash_stats["profit"]
            ),
            fg=get_result_color(
                cash_stats["profit"]
            )
        )

        self.cash_profit_bb.config(
            text=(
                f"{cash_stats['profit_bb']:+.2f} BB"
                .replace(".", ",")
            ),
            fg=get_result_color(
                cash_stats["profit_bb"]
            )
        )

        self.cash_bb100.config(
            text=format_bb100(
                cash_stats["bb100"]
            ),
            fg=get_result_color(
                cash_stats["bb100"]
            )
        )

        # SESSION FILTRÉE

        self.session_hands.config(
            text=str(
                session_stats["hands"]
            )
        )

        self.session_profit.config(
            text=format_signed_money(
                session_stats["profit"]
            ),
            fg=get_result_color(
                session_stats["profit"]
            )
        )

        self.session_bb100.config(
            text=format_bb100(
                session_stats["bb100"]
            ),
            fg=get_result_color(
                session_stats["bb100"]
            )
        )

        self.session_duration.config(
            text=format_session_duration(
                session_stats["started_at"],
                session_stats["ended_at"]
            )
        )

        # MTT FILTRÉ

        self.mtt_count.config(
            text=str(
                mtt_stats["tournaments"]
            )
        )

        self.mtt_cost.config(
            text=format_money(
                mtt_stats["total_cost"]
            )
        )

        self.mtt_average_buyin.config(
            text=format_money(
                mtt_stats["average_buyin"]
            )
        )

        self.mtt_imported_prizes.config(
            text=format_money(
                mtt_stats["imported_prizes"]
            )
        )

        self.mtt_corrections.config(
            text=format_signed_money(
                mtt_stats["corrections"]
            ),
            fg=get_result_color(
                mtt_stats["corrections"]
            )
        )

        self.mtt_profit.config(
            text=format_signed_money(
                mtt_stats["profit"]
            ),
            fg=get_result_color(
                mtt_stats["profit"]
            )
        )

        self.mtt_roi.config(
            text=format_percentage(
                mtt_stats["roi"]
            ),
            fg=get_result_color(
                mtt_stats["roi"]
            )
        )

        self.mtt_itm.config(
            text=(
                f"{mtt_stats['itm_rate']:.2f} %"
                .replace(".", ",")
            )
        )

        # BANKROLL

        self.bankroll_limit.config(
            text=(
                plan[
                    "recommended_limit"
                ]
            )
        )

        if plan[
            "next_limit"
        ] is None:

            self.bankroll_next.config(
                text="Aucune"
            )

            self.bankroll_target.config(
                text="—"
            )

            self.bankroll_missing.config(
                text="0,00 $"
            )

        else:

            self.bankroll_next.config(
                text=plan[
                    "next_limit"
                ]
            )

            self.bankroll_target.config(
                text=format_money(
                    plan[
                        "next_required"
                    ]
                )
            )

            self.bankroll_missing.config(
                text=format_money(
                    plan[
                        "amount_needed"
                    ]
                )
            )

    # =====================================================
    # RUN
    # =====================================================

    def run(
        self
    ) -> None:

        self.window.mainloop()


def start_tracker(
) -> None:

    application = (
        TrackerApplication()
    )

    application.run()