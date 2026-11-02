"""Step definitions – Épico 2: Detecção e Rastreamento de Pessoas (US-003, US-004)."""
from behave import given, when, then
from features.steps.shared_steps import mock_frame

try:
    from src.detection.person import PersonDetector
except ImportError:
    PersonDetector = None

try:
    from src.tracking.tracker import PersonTracker
except ImportError:
    PersonTracker = None


# ── US-003: Detectar pessoas na imagem ────────────────────────────────────
# O step When 'o sistema analisa o quadro' está definido em shared_steps.py

@given('que um quadro de vídeo com uma pessoa visível está disponível')
def step_frame_one_person(context):
    assert PersonDetector is not None, \
        "Implemente src.detection.person.PersonDetector"
    context.detector = PersonDetector()
    context.frame = mock_frame()       # substituir por fixture real com pessoa

@given('que um quadro de vídeo contém uma pessoa parcialmente fora do enquadramento')
def step_frame_partial_person(context):
    assert PersonDetector is not None, \
        "Implemente src.detection.person.PersonDetector"
    context.detector = PersonDetector()
    context.frame = mock_frame()       # frame com pessoa cortada na borda

@given('que um quadro de vídeo contém múltiplas pessoas')
def step_frame_multiple_persons(context):
    assert PersonDetector is not None, \
        "Implemente src.detection.person.PersonDetector"
    context.detector = PersonDetector()
    context.frame = mock_frame()       # frame com 3+ pessoas

@then('uma caixa delimitadora é desenhada ao redor da pessoa detectada')
def step_person_has_bbox(context):
    assert len(context.detections) > 0, "Nenhuma pessoa detectada no quadro"
    assert all(d.bbox is not None for d in context.detections), \
        "Toda detecção deve conter uma caixa delimitadora (bbox)"

@then('a pessoa parcialmente visível é detectada com caixa delimitadora')
def step_partial_person_detected(context):
    assert len(context.detections) > 0, \
        "Pessoa parcialmente visível não foi detectada"
    assert context.detections[0].bbox is not None, \
        "Detecção de pessoa parcial deve conter bbox"

@then('cada pessoa detectada recebe um identificador temporário único')
def step_persons_have_unique_ids(context):
    assert len(context.detections) > 0, "Nenhuma pessoa detectada"
    ids = [d.track_id for d in context.detections]
    assert len(ids) == len(set(ids)), \
        f"IDs duplicados encontrados: {ids}"


# ── US-004: Rastrear pessoas entre quadros ────────────────────────────────

@given('que uma pessoa é detectada no quadro atual')
def step_person_in_current_frame(context):
    assert PersonTracker is not None, \
        "Implemente src.tracking.tracker.PersonTracker"
    context.tracker = PersonTracker()
    context.frame_a = mock_frame()
    result = context.tracker.update(context.frame_a)
    context.initial_id = result[0].track_id if result else None

@given('que uma pessoa com ID "{person_id}" está sendo rastreada')
def step_person_tracked_with_id(context, person_id):
    assert PersonTracker is not None, \
        "Implemente src.tracking.tracker.PersonTracker"
    context.tracker = PersonTracker()
    context.expected_id = int(person_id)
    context.frame = mock_frame()

@given('que um quadro de vídeo contém "{n}" pessoas detectadas')
def step_frame_n_persons(context, n):
    assert PersonTracker is not None, \
        "Implemente src.tracking.tracker.PersonTracker"
    context.tracker = PersonTracker()
    context.expected_person_count = int(n)
    context.frame = mock_frame()

@when('o sistema processa o quadro seguinte com a mesma pessoa')
def step_process_next_frame(context):
    context.frame_b = mock_frame()
    context.next_frame_result = context.tracker.update(context.frame_b)

@when('a pessoa permanece visível por "{n}" quadros consecutivos')
def step_person_visible_n_frames(context, n):
    context.tracking_results = []
    for _ in range(int(n)):
        result = context.tracker.update(context.frame)
        context.tracking_results.append(result)

@when('o sistema processa os quadros seguintes')
def step_process_subsequent_frames(context):
    context.tracking_history = []
    for _ in range(10):
        result = context.tracker.update(context.frame)
        context.tracking_history.append(result)

@then('a pessoa mantém o mesmo ID entre os dois quadros')
def step_id_consistent_between_frames(context):
    assert context.initial_id is not None, "Nenhuma pessoa rastreada no quadro inicial"
    assert len(context.next_frame_result) > 0, "Nenhuma pessoa rastreada no quadro seguinte"
    assert context.next_frame_result[0].track_id == context.initial_id, (
        f"ID mudou entre quadros: {context.initial_id} → "
        f"{context.next_frame_result[0].track_id}"
    )

@then('o ID "{person_id}" permanece associado à mesma pessoa durante todos os quadros')
def step_id_stable_across_frames(context, person_id):
    expected = int(person_id)
    for i, frame_result in enumerate(context.tracking_results):
        ids = [r.track_id for r in frame_result]
        assert expected in ids, \
            f"ID {expected} não encontrado no quadro {i + 1}: IDs presentes = {ids}"

@then('cada uma das "{n}" pessoas mantém seu próprio ID persistente e distinto')
def step_multiple_ids_stable(context, n):
    expected_count = int(n)
    all_ids_per_frame = [
        {r.track_id for r in frame_result}
        for frame_result in context.tracking_history
    ]
    for i, ids in enumerate(all_ids_per_frame):
        assert len(ids) == expected_count, (
            f"Quadro {i + 1}: esperado {expected_count} IDs distintos, obtidos {len(ids)}"
        )
