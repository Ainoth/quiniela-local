"""Compatibilidad; implementación en la arquitectura modular."""
import importlib
import sys
sys.modules[__name__] = importlib.import_module("quiniela_ai_studio.ui.window")
