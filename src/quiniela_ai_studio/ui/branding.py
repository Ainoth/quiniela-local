"""Identidad de escritorio e icono distribuido con la interfaz Qt."""

import sys
from importlib.resources import files

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

APPLICATION_ID = 'quiniela-ai-studio'


def configure_application(application: QApplication) -> None:
    """Identifica ventanas y diálogos y carga el icono también desde una wheel."""
    if sys.platform == 'win32':
        import ctypes

        # Identidad estable para agrupar las ventanas en la barra de Windows.
        set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        result = set_app_id('QuinielaAIStudio.Desktop')
        if result < 0:
            raise OSError(f'No se pudo establecer la identidad de escritorio: {result}')

    application.setApplicationName(APPLICATION_ID)
    application.setApplicationDisplayName('Quiniela AI Studio')
    application.setDesktopFileName(APPLICATION_ID)
    data = files('quiniela_ai_studio.ui').joinpath('assets/quiniela-local.png').read_bytes()
    pixmap = QPixmap()
    if not pixmap.loadFromData(data, 'PNG'):
        raise RuntimeError('No se pudo cargar el icono de Quiniela AI Studio.')
    application.setWindowIcon(QIcon(pixmap.scaled(
        256, 256, Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )))
