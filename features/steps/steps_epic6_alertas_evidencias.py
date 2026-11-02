"""Step definitions – Épico 6: Alertas e Evidências (US-013, US-014, US-015, US-016)."""
import os
from behave import given, when, then
from features.steps.shared_steps import mock_frame

try:
    from src.alerts.visual import VisualAlertRenderer
except ImportError:
    VisualAlertRenderer = None

try:
    from src.alerts.evidence import EvidenceRecorder
except ImportError:
    EvidenceRecorder = None

try:
    from src.notifications.notifier import NotificationService
except ImportError:
    NotificationService = None


def _make_violation(person_id, reason='sem capacete'):
    from types import SimpleNamespace
    return SimpleNamespace(person_id=person_id, reason=reason)


# ── US-013: Exibir alerta visual ──────────────────────────────────────────

@given('que uma não conformidade de EPI é detectada para a pessoa de ID "{person_id}"')
def step_noncompliance_for_person(context, person_id):
    assert VisualAlertRenderer is not None, \
        "Implemente src.alerts.visual.VisualAlertRenderer"
    context.renderer = VisualAlertRenderer()
    context.violation = _make_violation(int(person_id))
    context.frame = mock_frame()

@when('o quadro de vídeo é renderizado')
def step_render_frame(context):
    context.rendered_frame = context.renderer.render(
        context.frame, [context.violation]
    )

@then('a caixa delimitadora da pessoa de ID "{person_id}" é exibida na cor vermelha')
def step_bbox_red(context, person_id):
    assert context.rendered_frame is not None, \
        "VisualAlertRenderer.render() deve retornar o frame anotado"
    color = context.renderer.get_bbox_color(context.rendered_frame, int(person_id))
    assert color == (0, 0, 255), \
        f"Cor da bbox para pessoa {person_id} deve ser vermelha (0,0,255), obtida: {color}"

@then('o motivo do alerta, como "{reason}", é exibido próximo à caixa delimitadora')
def step_alert_reason_displayed(context, reason):
    labels = context.renderer.get_labels(context.rendered_frame)
    assert any(reason.lower() in lbl.lower() for lbl in labels), (
        f"Motivo '{reason}' não encontrado nos rótulos exibidos: {labels}"
    )


# ── US-014: Registrar imagem da ocorrência ────────────────────────────────

@given('que uma não conformidade de EPI é detectada')
def step_noncompliance_detected(context):
    assert EvidenceRecorder is not None, \
        "Implemente src.alerts.evidence.EvidenceRecorder"
    context.recorder = EvidenceRecorder()
    context.violation = _make_violation(person_id=1)
    context.frame = mock_frame()

@when('o alerta é emitido')
def step_alert_emitted(context):
    context.saved_image_path = context.recorder.save_image(
        context.frame, context.violation
    )

@when('o alerta é emitido e a imagem é salva')
def step_alert_emitted_image_saved(context):
    context.saved_image_path = context.recorder.save_image(
        context.frame, context.violation
    )

@then('o sistema salva uma imagem do quadro em disco')
def step_image_saved_to_disk(context):
    assert context.saved_image_path is not None, \
        "EvidenceRecorder.save_image() deve retornar o caminho do arquivo"
    assert os.path.isfile(context.saved_image_path), \
        f"Arquivo de imagem não encontrado em: {context.saved_image_path}"

@then('a imagem contém sobreposição visual com a data e hora do evento')
def step_image_has_timestamp(context):
    metadata = context.recorder.get_image_metadata(context.saved_image_path)
    assert metadata.timestamp is not None, \
        "Metadados da imagem devem incluir timestamp"


# ── US-015: Registrar vídeo da ocorrência ────────────────────────────────

@given('que o período pré-alerta está configurado como "{seconds}" segundos')
def step_pre_alert_seconds(context, seconds):
    assert EvidenceRecorder is not None, \
        "Implemente src.alerts.evidence.EvidenceRecorder"
    context.pre_seconds = int(seconds)
    context.recorder = EvidenceRecorder(
        pre_alert_seconds=context.pre_seconds,
        post_alert_seconds=0,
    )
    context.violation = _make_violation(person_id=1)

@given('que o período pós-alerta está configurado como "{seconds}" segundos')
def step_post_alert_seconds(context, seconds):
    assert EvidenceRecorder is not None, \
        "Implemente src.alerts.evidence.EvidenceRecorder"
    context.post_seconds = int(seconds)
    context.recorder = EvidenceRecorder(
        pre_alert_seconds=0,
        post_alert_seconds=context.post_seconds,
    )
    context.violation = _make_violation(person_id=1)

@when('uma ocorrência de não conformidade é registrada')
def step_occurrence_recorded(context):
    context.saved_video_path = context.recorder.save_video(context.violation)

@then('o arquivo de vídeo salvo contém os "{seconds}" segundos anteriores ao alerta')
def step_video_has_pre_seconds(context, seconds):
    assert context.saved_video_path is not None, \
        "EvidenceRecorder.save_video() deve retornar o caminho do arquivo"
    meta = context.recorder.get_video_metadata(context.saved_video_path)
    assert meta.pre_alert_seconds >= int(seconds), (
        f"Vídeo deve conter ao menos {seconds}s antes do alerta, "
        f"contém: {meta.pre_alert_seconds}s"
    )

@then('o arquivo de vídeo salvo contém os "{seconds}" segundos posteriores ao alerta')
def step_video_has_post_seconds(context, seconds):
    assert context.saved_video_path is not None, \
        "EvidenceRecorder.save_video() deve retornar o caminho do arquivo"
    meta = context.recorder.get_video_metadata(context.saved_video_path)
    assert meta.post_alert_seconds >= int(seconds), (
        f"Vídeo deve conter ao menos {seconds}s após o alerta, "
        f"contém: {meta.post_alert_seconds}s"
    )


# ── US-016: Enviar notificação automática ─────────────────────────────────

@given('que a integração com Telegram está configurada')
def step_telegram_configured(context):
    assert NotificationService is not None, \
        "Implemente src.notifications.notifier.NotificationService"
    context.notifier = NotificationService(channels=['telegram'])
    context.violation = _make_violation(person_id=1)
    context.image_path = None

@given('que a integração com e-mail está configurada')
def step_email_configured(context):
    assert NotificationService is not None, \
        "Implemente src.notifications.notifier.NotificationService"
    context.notifier = NotificationService(channels=['email'])
    context.violation = _make_violation(person_id=1)
    context.image_path = None

@given('que a integração de notificação está configurada')
def step_notification_configured(context):
    assert NotificationService is not None, \
        "Implemente src.notifications.notifier.NotificationService"
    context.notifier = NotificationService(channels=['telegram', 'email'])
    context.violation = _make_violation(person_id=1)
    context.image_path = 'tests/fixtures/sample_violation.jpg'

@when('uma não conformidade de EPI é detectada')
def step_noncompliance_event(context):
    context.notification_result = context.notifier.send(
        violation=context.violation,
        image_path=context.image_path,
    )

@when('uma não conformidade de EPI é detectada e o alerta é enviado')
def step_noncompliance_with_send(context):
    context.notification_result = context.notifier.send(
        violation=context.violation,
        image_path=context.image_path,
    )

@then('o sistema envia uma mensagem de alerta para o canal do Telegram configurado')
def step_telegram_sent(context):
    assert context.notification_result.telegram_sent, \
        "Notificação Telegram não foi enviada"

@then('o sistema envia um e-mail de alerta para o destinatário configurado')
def step_email_sent(context):
    assert context.notification_result.email_sent, \
        "Notificação por e-mail não foi enviada"

@then('a notificação inclui a imagem capturada da ocorrência como anexo ou inline')
def step_notification_has_image(context):
    assert context.notification_result.image_attached, \
        "Notificação deve incluir imagem da ocorrência"
