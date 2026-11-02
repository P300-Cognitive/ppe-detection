"""Step definitions – Épico 3: Detecção de EPI (US-005, US-006, US-007)."""
from behave import given, when, then
from features.steps.shared_steps import mock_frame

try:
    from src.detection.ppe import PPEDetector
except ImportError:
    PPEDetector = None


def _ppe_detector(*classes):
    assert PPEDetector is not None, \
        "Implemente src.detection.ppe.PPEDetector"
    return PPEDetector(classes=list(classes))


# ── US-005: Detectar capacetes ────────────────────────────────────────────
# When 'o sistema analisa o quadro' → shared_steps.py

@given('que um quadro de vídeo contém uma pessoa usando capacete')
def step_frame_person_with_helmet(context):
    context.detector = _ppe_detector('helmet')
    context.frame = mock_frame()

@given('que um capacete é detectado no quadro')
def step_helmet_already_detected(context):
    context.detector = _ppe_detector('helmet')
    context.frame = mock_frame()

@given('que um quadro contém um capacete de cor {cor}')
def step_frame_colored_helmet(context, cor):
    context.detector = _ppe_detector('helmet')
    context.helmet_color = cor
    context.frame = mock_frame()

@when('o sistema exibe o resultado da detecção')
def step_display_detection_result(context):
    context.rendered = context.detector.render(context.frame, context.detections)

@then('uma caixa delimitadora é desenhada ao redor do capacete detectado')
def step_helmet_has_bbox(context):
    helmets = [d for d in context.detections if d.class_name == 'helmet']
    assert len(helmets) > 0, "Nenhum capacete detectado no quadro"
    assert all(d.bbox is not None for d in helmets), \
        "Todo capacete detectado deve ter caixa delimitadora"

@then('o valor de confiança da detecção é exibido junto à caixa delimitadora')
def step_confidence_displayed(context):
    helmets = [d for d in context.detections if d.class_name == 'helmet']
    assert len(helmets) > 0, "Nenhum capacete detectado"
    assert all(0.0 <= d.confidence <= 1.0 for d in helmets), \
        "Confiança deve ser um valor entre 0 e 1"
    assert context.rendered is not None, \
        "PPEDetector.render() deve retornar o frame anotado"

@then('o capacete {cor} é detectado com caixa delimitadora')
def step_colored_helmet_detected(context, cor):
    helmets = [d for d in context.detections if d.class_name == 'helmet']
    assert len(helmets) > 0, \
        f"Capacete de cor '{cor}' não foi detectado no quadro"
    assert all(d.bbox is not None for d in helmets), \
        "Todo capacete detectado deve ter caixa delimitadora"


# ── US-006: Detectar coletes refletivos ───────────────────────────────────

@given('que um quadro de vídeo contém uma pessoa usando colete refletivo de qualquer cor')
def step_frame_vest(context):
    context.detector = _ppe_detector('vest')
    context.frame = mock_frame()

@given('que um quadro contém "{n}" pessoas, sendo uma com colete e outra sem')
def step_frame_one_with_vest(context, n):
    context.detector = _ppe_detector('vest')
    context.person_count = int(n)
    context.frame = mock_frame()

@then('o colete é detectado com caixa delimitadora')
def step_vest_detected(context):
    vests = [d for d in context.detections if d.class_name == 'vest']
    assert len(vests) > 0, "Nenhum colete detectado no quadro"
    assert all(d.bbox is not None for d in vests), \
        "Colete detectado deve ter caixa delimitadora"

@then('o colete é associado apenas à pessoa que está utilizando o equipamento')
def step_vest_correct_person(context):
    vests = [d for d in context.detections if d.class_name == 'vest']
    assert len(vests) == 1, \
        f"Apenas 1 colete deveria ser detectado, mas foram encontrados {len(vests)}"


# ── US-007: Detectar outros EPIs ──────────────────────────────────────────

def _setup_ppe_frame(context, ppe_class):
    context.expected_ppe_class = ppe_class
    context.detector = _ppe_detector(ppe_class)
    context.frame = mock_frame()


@given('que um quadro de vídeo contém uma pessoa usando óculos de proteção')
def step_frame_with_glasses(context):
    _setup_ppe_frame(context, 'glasses')

@given('que um quadro de vídeo contém uma pessoa usando máscara de proteção')
def step_frame_with_mask(context):
    _setup_ppe_frame(context, 'mask')

@given('que um quadro de vídeo contém uma pessoa usando luvas de proteção')
def step_frame_with_gloves(context):
    _setup_ppe_frame(context, 'gloves')

@given('que um quadro de vídeo contém uma pessoa usando botas de segurança')
def step_frame_with_boots(context):
    _setup_ppe_frame(context, 'boots')

@given('que um quadro de vídeo contém uma pessoa usando múltiplos EPIs')
def step_frame_multiple_ppe(context):
    context.detector = _ppe_detector('helmet', 'vest', 'glasses', 'mask', 'gloves', 'boots')
    context.frame = mock_frame()

@then('o EPI "{epi_name}" é identificado individualmente com caixa delimitadora')
def step_ppe_individually_detected(context, epi_name):
    matches = [d for d in context.detections if d.class_name == epi_name]
    assert len(matches) > 0, \
        f"EPI '{epi_name}' não foi detectado no quadro"
    assert all(d.bbox is not None for d in matches), \
        f"EPI '{epi_name}' deve ter caixa delimitadora"

@then('o sistema informa quais EPIs foram encontrados para cada pessoa detectada')
def step_ppe_list_reported(context):
    assert len(context.detections) > 0, "Nenhuma detecção retornada"
    for det in context.detections:
        assert hasattr(det, 'class_name'), \
            "Cada detecção deve informar o nome da classe do EPI"
        assert hasattr(det, 'person_id'), \
            "Cada detecção deve estar associada a uma pessoa (person_id)"
