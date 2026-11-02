"""Steps reutilizados por múltiplos épicos."""
import numpy as np
from behave import given, when, then


def mock_frame(height=480, width=640):
    """Cria um frame BGR vazio para uso nos testes."""
    return np.zeros((height, width, 3), dtype=np.uint8)


# ── Shared: análise de quadro (US-003, US-005, US-006, US-007) ─────────────

@when('o sistema analisa o quadro')
def step_analyze_frame(context):
    assert hasattr(context, 'detector'), (
        "O step Given deve configurar context.detector antes de "
        "'o sistema analisa o quadro'"
    )
    assert hasattr(context, 'frame'), (
        "O step Given deve configurar context.frame antes de "
        "'o sistema analisa o quadro'"
    )
    context.detections = context.detector.detect(context.frame)


# ── Shared: associação pessoa x EPI (US-008, US-009) ──────────────────────

@when('o sistema realiza a associação de EPIs')
def step_associate_ppe(context):
    assert hasattr(context, 'associator'), (
        "O step Given deve configurar context.associator"
    )
    context.associations = context.associator.associate(
        context.persons, context.ppe_detections
    )


# ── Shared: limiar de confirmação (US-010, US-011) ────────────────────────

@given('o limiar de confirmação está configurado como "{n}" quadros consecutivos')
def step_set_confirmation_threshold(context, n):
    context.confirmation_threshold = int(n)
