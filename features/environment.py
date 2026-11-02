"""Configuração global do ambiente behave."""
import logging
import os
import sys

# Garante que src/ seja importável sem instalação de pacote
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Modo de teste: notificações são simuladas, sem chamadas de rede reais
os.environ.setdefault("PPE_TEST_MODE", "1")


def before_all(context):
    context.config.setup_logging()
    logging.basicConfig(level=logging.WARNING)


def before_scenario(context, scenario):
    context.capture = None
    context.capture_error = None
    context.detections = []
    context.associations = {}


def after_scenario(context, scenario):
    capture = getattr(context, "capture", None)
    if capture is not None:
        try:
            capture.stop()
        except Exception:
            pass
