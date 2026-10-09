import argparse
import os
from pathlib import Path
import sys
from . import __version__
from .storage import Repository
from .demo import demo_round


def default_data_dir():
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'QuinielaAIStudio'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')) / 'quiniela-ai-studio'


def main():
    parser = argparse.ArgumentParser(description='Quiniela AI Studio — escritorio local')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--data-dir', type=Path, default=default_data_dir())
    parser.add_argument('--self-check', action='store_true', help='Comprueba SQLite y cálculos sin abrir ventanas.')
    parser.add_argument('--smoke-test', action='store_true', help='Abre Qt y cierra automáticamente para comprobar instalación.')
    args = parser.parse_args()
    repository = Repository(args.data_dir / 'studio.sqlite3')
    if not repository.rounds():
        repository.save_round(demo_round())
    if args.self_check:
        from .engine import generate, coverage_template, size, evaluate
        bets=generate(('1X','1','1X2')+('1',)*11,'M1')
        assert len(bets)==6
        assert size(coverage_template(('1',)*14,(False,)*14,10))==3456
        assert evaluate(bets,'-'*14)['known']==0
        assert repository.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        print('v0.1 OK: SQLite íntegro · ejemplo 6 columnas · nivel 10 = 3456 · pendientes correctos')
        repository.close();return 0
    if sys.platform.startswith('linux') and os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
        import ctypes
        try:
            ctypes.CDLL('libxcb-cursor.so.0')
        except OSError:
            local = Path(sys.prefix) / 'qt-runtime' / 'usr' / 'lib'
            candidates = list(local.glob('*/libxcb-cursor.so.0'))
            if candidates and not os.environ.get('QUINIELA_QT_RUNTIME'):
                environment = dict(os.environ)
                environment['LD_LIBRARY_PATH'] = str(candidates[0].parent) + ':' + environment.get('LD_LIBRARY_PATH', '')
                environment['QUINIELA_QT_RUNTIME'] = '1'
                repository.close()
                os.execve(sys.executable, [sys.executable, '-m', 'quiniela_studio', *sys.argv[1:]], environment)
            repository.close()
            print('Falta libxcb-cursor0 para Qt/X11. Ejecuta ./run_studio.sh o instala libxcb-cursor0 con el gestor de paquetes.', file=sys.stderr)
            return 1
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
        from .ui import MainWindow, STYLE
    except ImportError:
        repository.close()
        print('Instala la interfaz: python -m pip install -e .', file=sys.stderr)
        return 1
    application=QApplication(sys.argv[:1]);application.setStyle('Fusion');application.setStyleSheet(STYLE)
    window=MainWindow(repository);window.show()
    if args.smoke_test:QTimer.singleShot(700,window.close)
    return application.exec()


if __name__ == '__main__':
    raise SystemExit(main())
