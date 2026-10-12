"""Explain where an exported TXT is and how to use it outside the app."""

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from quiniela_ai_studio.domain.models import Round, SystemVersion

UPLOAD_URL = "https://www.eduardolosilla.es/quiniela/archivos"


def _count(quantity: int) -> str:
    return f"{quantity:,}".replace(",", ".")


def _money(cents: int) -> str:
    return f"{_count(cents // 100)},{cents % 100:02} €"


def build_export_dialog(
    parent: QWidget | None,
    path: Path,
    system: SystemVersion,
    round_: Round,
    quantity: int,
) -> QDialog:
    """Build a receipt; opening a folder or website always needs a button click.

    ``quantity`` is the final exported number, including copies and Pleno pairs.
    The caller supplies the frozen round used to price that exported file.
    Creating this dialog does not start an external action or contact a server.
    """
    if type(quantity) is not int or quantity < 1:
        raise ValueError("El archivo debe contener al menos una apuesta.")
    if system.round_key != round_.key:
        raise ValueError("El archivo y la jornada deben pertenecer a la misma quiniela.")

    path = path.resolve()
    dialog = QDialog(parent)
    dialog.setWindowTitle("TXT guardado: dónde está y cómo usarlo")
    dialog.setMinimumWidth(540)
    dialog.resize(660, 420)
    layout = QVBoxLayout(dialog)

    def label(text: str, name: str) -> QLabel:
        widget = QLabel(text)
        widget.setObjectName(name)
        widget.setTextFormat(Qt.TextFormat.PlainText)
        widget.setWordWrap(True)
        widget.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        layout.addWidget(widget)
        return widget

    status = label(
        "Archivo guardado. Las apuestas todavía no están jugadas.", "exportStatus"
    )
    font = status.font()
    font.setBold(True)
    status.setFont(font)
    exported_plenos = (
        tuple(dict.fromkeys(bet.pleno for bet in system.bets if bet.pleno))
        if system.bets
        else system.plenos
    )
    goals = ", ".join(f"{pair[0]}–{pair[1]}" for pair in exported_plenos)
    pleno_text = (
        f"Pleno al 15: {goals}. M significa 3 o más goles."
        if goals
        else "Pleno al 15: sin resultado elegido."
    )
    label(
        f"Quiniela: {system.name}\n"
        f"Temporada: {round_.season} · Jornada: {round_.number}\n"
        f"Apuestas del TXT: {_count(quantity)} "
        "(incluye las copias y los Plenos de las apuestas guardadas)\n"
        f"{pleno_text}\n"
        f"Coste según tu quiniela: {_money(quantity * round_.price_cents)} "
        f"({_money(round_.price_cents)} por apuesta).",
        "exportSummary",
    )
    label("Tu archivo está aquí:", "exportPathLabel")
    path_input = QLineEdit(str(path))
    path_input.setObjectName("exportPath")
    path_input.setReadOnly(True)
    path_input.setCursorPosition(0)
    layout.addWidget(path_input)

    available = (
        round_.season != "DEMO" and round_.mode == "current" and round_.editable
    )
    if available:
        availability = (
            "Abre la web de Quinielista para cargar este TXT. "
            "Revisa allí la jornada, las apuestas y el precio antes de pagar."
        )
    elif round_.season == "DEMO" or round_.mode == "simulation":
        availability = (
            "Esta quiniela es de demostración. Puedes guardar el TXT para probar, "
            "pero no jugar estas apuestas."
        )
    elif round_.mode == "future":
        availability = (
            "Esta jornada aún no está en curso. Puedes conservar el archivo; "
            "la opción de jugar estará disponible para la jornada en curso."
        )
    else:
        availability = (
            "Esta jornada ya no permite jugar. Puedes conservar el archivo "
            "y consultar tus apuestas."
        )
    label(availability, "exportAvailability")
    instructions = (
        "1. Abre la web con el botón de abajo.\n"
        f"2. Comprueba la temporada {round_.season} y la jornada {round_.number}.\n"
        f"3. Elige el archivo TXT: {path.name}.\n"
        f"4. Indica {_count(quantity)} apuestas y revisa el precio y el Pleno.\n"
        "5. Confirma y paga en la web cuando esté todo correcto."
        if available
        else "Para jugar, crea una quiniela de la jornada en curso."
    )
    label(instructions, "exportInstructions")

    actions = QHBoxLayout()
    folder_button = QPushButton("Abrir carpeta")
    folder_button.setObjectName("openExportFolder")
    folder_button.setAutoDefault(False)
    folder_button.clicked.connect(
        lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
    )
    actions.addWidget(folder_button)
    web_button = QPushButton("Abrir web para cargar el TXT")
    web_button.setObjectName("openExportWebsite")
    web_button.setAutoDefault(False)
    web_button.setEnabled(available)
    web_button.setToolTip(availability)
    web_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(UPLOAD_URL)))
    actions.addWidget(web_button)
    layout.addLayout(actions)

    closing = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    close_button = closing.button(QDialogButtonBox.StandardButton.Close)
    close_button.setText("Cerrar")
    close_button.setObjectName("exportClose")
    close_button.setDefault(True)
    closing.rejected.connect(dialog.reject)
    layout.addWidget(closing)
    return dialog
