"""Step definitions – Épico 5: Regras de Segurança (US-010, US-011, US-012)."""
from behave import given, when, then

try:
    from src.rules.engine import SafetyRulesEngine
except ImportError:
    SafetyRulesEngine = None


def _engine():
    assert SafetyRulesEngine is not None, \
        "Implemente src.rules.engine.SafetyRulesEngine"
    return SafetyRulesEngine()


# ── US-010: Identificar ausência de capacete ──────────────────────────────
# And 'o limiar de confirmação está configurado como ...' → shared_steps.py

@given('que uma pessoa é detectada sem capacete')
def step_person_without_helmet(context):
    context.engine = _engine()
    context.missing_ppe = 'helmet'
    context.person_id = 1

@when('a pessoa permanece sem capacete por "{n}" quadros consecutivos')
def step_person_missing_helmet_n_frames(context, n):
    for _ in range(int(n)):
        context.engine.evaluate(
            person_id=context.person_id,
            missing_ppe=context.missing_ppe,
            threshold=context.confirmation_threshold,
        )
    context.alert = context.engine.get_pending_alert(context.person_id)

@when('a pessoa está sem capacete por apenas "{n}" quadros consecutivos')
def step_person_missing_helmet_few_frames(context, n):
    for _ in range(int(n)):
        context.engine.evaluate(
            person_id=context.person_id,
            missing_ppe=context.missing_ppe,
            threshold=context.confirmation_threshold,
        )
    context.alert = context.engine.get_pending_alert(context.person_id)

@given('que "{total}" pessoas estão no quadro e apenas a de ID "{violator_id}" está sem capacete')
def step_multiple_persons_one_violator(context, total, violator_id):
    context.engine = _engine()
    context.total_persons = int(total)
    context.violator_id = int(violator_id)
    context.missing_ppe = 'helmet'

@when('o sistema emite o alerta de ausência de capacete')
def step_emit_helmet_alert(context):
    context.engine.evaluate(
        person_id=context.violator_id,
        missing_ppe=context.missing_ppe,
        threshold=1,
    )
    context.alert = context.engine.get_pending_alert(context.violator_id)

@then('o sistema emite um alerta de ausência de capacete')
def step_helmet_alert_emitted(context):
    assert context.alert is not None, \
        "Nenhum alerta emitido após o limiar de confirmação ser atingido"
    assert context.alert.ppe_type == 'helmet', \
        f"Tipo do alerta deve ser 'helmet', obtido: {context.alert.ppe_type}"

@then('nenhum alerta de ausência de capacete é emitido')
def step_no_helmet_alert(context):
    assert context.alert is None, \
        "Alerta foi emitido antes de atingir o limiar de confirmação"

@then('o alerta indica especificamente a pessoa de ID "{person_id}" como infratora')
def step_alert_identifies_person(context, person_id):
    assert context.alert is not None, "Nenhum alerta foi emitido"
    assert context.alert.person_id == int(person_id), (
        f"Alerta deve identificar pessoa {person_id}, "
        f"mas identificou {context.alert.person_id}"
    )


# ── US-011: Identificar ausência de colete ────────────────────────────────

@given('que uma pessoa é detectada sem colete')
def step_person_without_vest(context):
    context.engine = _engine()
    context.missing_ppe = 'vest'
    context.person_id = 1

@when('a pessoa permanece sem colete por "{n}" quadros consecutivos')
def step_person_missing_vest_n_frames(context, n):
    for _ in range(int(n)):
        context.engine.evaluate(
            person_id=context.person_id,
            missing_ppe=context.missing_ppe,
            threshold=context.confirmation_threshold,
        )
    context.alert = context.engine.get_pending_alert(context.person_id)

@then('o sistema emite um alerta de ausência de colete')
def step_vest_alert_emitted(context):
    assert context.alert is not None, \
        "Nenhum alerta emitido após o limiar de confirmação ser atingido"
    assert context.alert.ppe_type == 'vest', \
        f"Tipo do alerta deve ser 'vest', obtido: {context.alert.ppe_type}"

@given('que o sistema emitiu um alerta de ausência de colete para a pessoa de ID "{person_id}"')
def step_vest_alert_was_emitted(context, person_id):
    context.engine = _engine()
    context.alert_person_id = int(person_id)
    context.engine.force_alert(person_id=int(person_id), ppe_type='vest')

@when('o alerta é processado')
def step_alert_processed(context):
    context.engine.process_alerts()

@then('o evento é registrado no sistema com identificador da pessoa, câmera e timestamp')
def step_event_recorded(context):
    events = context.engine.get_recorded_events()
    matching = [e for e in events if e.person_id == context.alert_person_id]
    assert len(matching) > 0, \
        f"Nenhum evento registrado para pessoa {context.alert_person_id}"
    event = matching[-1]
    assert event.camera_id is not None, "Evento deve conter camera_id"
    assert event.timestamp is not None, "Evento deve conter timestamp"


# ── US-012: Configurar regras por ambiente ────────────────────────────────

@given('que o administrador acessa a configuração da câmera "{camera_id}"')
def step_access_camera_config(context, camera_id):
    context.engine = _engine()
    context.camera_id = camera_id

@when('define que o EPI "{ppe_type}" é obrigatório para essa câmera')
def step_set_required_ppe(context, ppe_type):
    context.engine.set_required_ppe(context.camera_id, [ppe_type])
    context.configured_ppe = ppe_type

@then('a câmera "{camera_id}" passa a exigir o uso de capacete nas detecções')
def step_camera_requires_helmet(context, camera_id):
    required = context.engine.get_required_ppe(camera_id)
    expected = getattr(context, 'configured_ppe', 'capacete')
    assert expected in required, \
        f"Câmera {camera_id} não exige '{expected}'. Regras atuais: {required}"

@given('que "{cam1}" exige apenas capacete')
def step_cam1_requires_helmet(context, cam1):
    context.engine = _engine()
    context.engine.set_required_ppe(cam1, ['helmet'])
    context.cam1 = cam1

@given('"{cam2}" exige capacete e colete')
def step_cam2_requires_helmet_vest(context, cam2):
    context.engine.set_required_ppe(cam2, ['helmet', 'vest'])
    context.cam2 = cam2

@when('o sistema avalia conformidade em cada câmera')
def step_evaluate_each_camera(context):
    context.rules_cam1 = context.engine.get_required_ppe(context.cam1)
    context.rules_cam2 = context.engine.get_required_ppe(context.cam2)

@then('"{cam1}" alerta apenas ausência de capacete')
def step_cam1_only_helmet_rule(context, cam1):
    assert context.rules_cam1 == ['helmet'], \
        f"Câmera {cam1} deve exigir apenas capacete: {context.rules_cam1}"

@then('"{cam2}" alerta ausência de capacete ou de colete')
def step_cam2_helmet_and_vest_rules(context, cam2):
    assert 'helmet' in context.rules_cam2, \
        f"Câmera {cam2} deve exigir capacete"
    assert 'vest' in context.rules_cam2, \
        f"Câmera {cam2} deve exigir colete"

@when('define como obrigatórios os EPIs "{ppe_list}"')
def step_set_multiple_required_ppe(context, ppe_list):
    epis = [e.strip() for e in ppe_list.split(',')]
    context.engine.set_required_ppe(context.camera_id, epis)

@then('a câmera "{camera_id}" exige os três EPIs simultaneamente para conformidade')
def step_camera_requires_three_ppe(context, camera_id):
    required = context.engine.get_required_ppe(camera_id)
    assert len(required) == 3, \
        f"Câmera {camera_id} deve exigir exatamente 3 EPIs, mas exige: {required}"
