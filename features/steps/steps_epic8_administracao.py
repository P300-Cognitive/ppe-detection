"""Step definitions – Épico 8: Administração (US-020, US-021, US-022)."""
from behave import given, when, then

try:
    from src.admin.camera_manager import CameraManager
except ImportError:
    CameraManager = None

try:
    from src.admin.model_manager import ModelManager
except ImportError:
    ModelManager = None

try:
    from src.admin.threshold_manager import ThresholdManager
except ImportError:
    ThresholdManager = None


# ── US-020: Gerenciar câmeras ─────────────────────────────────────────────

@given('que o administrador acessa o módulo de gerenciamento de câmeras')
def step_access_camera_module(context):
    assert CameraManager is not None, \
        "Implemente src.admin.camera_manager.CameraManager"
    context.cam_manager = CameraManager()

@given('que uma câmera com URL RTSP está cadastrada')
def step_rtsp_camera_registered(context):
    assert CameraManager is not None, \
        "Implemente src.admin.camera_manager.CameraManager"
    context.cam_manager = CameraManager()
    context.cam_manager.register('rtsp://192.168.1.100/stream')
    context.registered_url = 'rtsp://192.168.1.100/stream'

@given('que uma câmera está com status desabilitado')
def step_camera_disabled(context):
    assert CameraManager is not None, \
        "Implemente src.admin.camera_manager.CameraManager"
    context.cam_manager = CameraManager()
    camera = context.cam_manager.register('rtsp://192.168.1.200/stream')
    context.cam_manager.disable(camera.id)
    context.camera_id = camera.id

@given('que uma câmera está com status habilitado')
def step_camera_enabled(context):
    assert CameraManager is not None, \
        "Implemente src.admin.camera_manager.CameraManager"
    context.cam_manager = CameraManager()
    camera = context.cam_manager.register('rtsp://192.168.1.201/stream')
    context.cam_manager.enable(camera.id)
    context.camera_id = camera.id

@when('cadastra uma nova câmera com URL RTSP "{rtsp_url}"')
def step_register_rtsp_camera(context, rtsp_url):
    context.new_camera = context.cam_manager.register(rtsp_url)
    context.rtsp_url = rtsp_url

@when('o administrador solicita teste de conectividade')
def step_test_connectivity(context):
    context.connectivity_status = context.cam_manager.test_connectivity(
        context.registered_url
    )

@when('o administrador habilita a câmera')
def step_enable_camera(context):
    context.cam_manager.enable(context.camera_id)

@when('o administrador desabilita a câmera')
def step_disable_camera(context):
    context.cam_manager.disable(context.camera_id)

@then('a câmera é registrada no sistema com a URL fornecida')
def step_camera_registered(context):
    assert context.new_camera is not None, \
        "register() deve retornar o objeto câmera criado"
    assert context.new_camera.rtsp_url == context.rtsp_url, (
        f"URL da câmera registrada deve ser '{context.rtsp_url}', "
        f"obtida: '{context.new_camera.rtsp_url}'"
    )

@then('o sistema retorna o status de conectividade da câmera')
def step_connectivity_returned(context):
    assert context.connectivity_status is not None, \
        "test_connectivity() deve retornar um status"
    assert hasattr(context.connectivity_status, 'is_reachable'), \
        "Status deve ter atributo 'is_reachable'"

@then('a câmera passa para o status habilitado e começa a ser monitorada')
def step_camera_now_enabled(context):
    camera = context.cam_manager.get(context.camera_id)
    assert camera.enabled is True, \
        f"Câmera {context.camera_id} deve estar habilitada"

@then('a câmera para de ser monitorada sem ser removida do sistema')
def step_camera_disabled_not_removed(context):
    camera = context.cam_manager.get(context.camera_id)
    assert camera is not None, "Câmera não deve ser removida ao desabilitar"
    assert camera.enabled is False, \
        f"Câmera {context.camera_id} deve estar desabilitada"


# ── US-021: Gerenciar modelos de IA ───────────────────────────────────────

@given('que o administrador acessa o módulo de gerenciamento de modelos')
def step_access_model_module(context):
    assert ModelManager is not None, \
        "Implemente src.admin.model_manager.ModelManager"
    context.model_manager = ModelManager()

@given('que o administrador tenta fazer upload de um arquivo inválido')
def step_invalid_model_file(context):
    assert ModelManager is not None, \
        "Implemente src.admin.model_manager.ModelManager"
    context.model_manager = ModelManager()
    context.invalid_file = 'not_a_model.txt'

@given('que um novo modelo foi carregado no sistema')
def step_new_model_loaded(context):
    assert ModelManager is not None, \
        "Implemente src.admin.model_manager.ModelManager"
    context.model_manager = ModelManager()
    context.new_model = context.model_manager.upload('tests/fixtures/model_v2.pt')

@when('realiza upload de um arquivo de modelo válido no formato ".pt"')
def step_upload_valid_model(context):
    context.uploaded_model = context.model_manager.upload('tests/fixtures/model_v1.pt')
    context.upload_error = None

@when('o arquivo é submetido ao sistema')
def step_submit_invalid_file(context):
    try:
        context.model_manager.upload(context.invalid_file)
        context.upload_error = None
    except Exception as exc:
        context.upload_error = str(exc)

@when('o administrador ativa o novo modelo')
def step_activate_new_model(context):
    context.model_manager.activate(context.new_model.id)

@then('o modelo é armazenado no sistema e listado como disponível')
def step_model_stored_and_listed(context):
    assert context.uploaded_model is not None, \
        "upload() deve retornar o modelo criado"
    available = context.model_manager.list_available()
    assert any(m.id == context.uploaded_model.id for m in available), \
        "Modelo enviado deve aparecer na lista de disponíveis"

@then('o sistema rejeita o arquivo e informa o motivo da invalidade')
def step_invalid_model_rejected(context):
    assert context.upload_error is not None, \
        "Sistema deve rejeitar arquivo inválido com exceção"
    assert len(context.upload_error) > 0, \
        "Mensagem de erro deve explicar o motivo da invalidade"

@then('o sistema passa a utilizar o novo modelo nas detecções sem necessidade de reinicialização')
def step_model_swapped_without_restart(context):
    active = context.model_manager.get_active()
    assert active.id == context.new_model.id, (
        f"Modelo ativo deve ser {context.new_model.id}, "
        f"obtido: {active.id}"
    )
    assert context.model_manager.is_running(), \
        "ModelManager deve permanecer em execução após troca de modelo"


# ── US-022: Configurar limiares de confiança ──────────────────────────────

@given('que o administrador acessa as configurações de limiares')
def step_access_threshold_settings(context):
    assert ThresholdManager is not None, \
        "Implemente src.admin.threshold_manager.ThresholdManager"
    context.threshold_mgr = ThresholdManager()

@given('que o limiar de "{ppe_class}" é "{value}"')
@given('o limiar de "{ppe_class}" é "{value}"')
def step_threshold_is(context, ppe_class, value):
    if not hasattr(context, 'threshold_mgr'):
        assert ThresholdManager is not None, \
            "Implemente src.admin.threshold_manager.ThresholdManager"
        context.threshold_mgr = ThresholdManager()
    context.threshold_mgr.set(ppe_class, float(value))

@given('que o sistema está em execução monitorando câmeras')
def step_system_running(context):
    assert ThresholdManager is not None, \
        "Implemente src.admin.threshold_manager.ThresholdManager"
    context.threshold_mgr = ThresholdManager()
    context.threshold_mgr.start()

@when('define o limiar de confiança da classe "{ppe_class}" como "{value}"')
def step_set_threshold(context, ppe_class, value):
    context.threshold_mgr.set(ppe_class, float(value))
    context.configured_class = ppe_class
    context.configured_value = float(value)

@when('o sistema realiza detecções no quadro')
def step_run_detections(context):
    context.active_thresholds = context.threshold_mgr.get_all()

@when('o administrador altera o limiar de confiança da classe "{ppe_class}" para "{value}"')
def step_update_threshold_live(context, ppe_class, value):
    context.threshold_mgr.set(ppe_class, float(value))
    context.updated_class = ppe_class
    context.updated_value = float(value)

@then('o sistema passa a usar "{value}" como confiança mínima para detectar capacetes')
def step_threshold_applied(context, value):
    current = context.threshold_mgr.get(context.configured_class)
    assert current == float(value), (
        f"Limiar de '{context.configured_class}' deve ser {value}, "
        f"obtido: {current}"
    )

@then('aplica limiar "{v1}" para capacetes e "{v2}" para coletes independentemente')
def step_independent_thresholds(context, v1, v2):
    helmet_th = context.active_thresholds.get('capacete')
    vest_th = context.active_thresholds.get('colete')
    assert helmet_th == float(v1), \
        f"Limiar de capacete deve ser {v1}, obtido: {helmet_th}"
    assert vest_th == float(v2), \
        f"Limiar de colete deve ser {v2}, obtido: {vest_th}"

@then('a alteração é aplicada imediatamente sem interromper o processamento de vídeo')
def step_threshold_hot_reload(context):
    current = context.threshold_mgr.get(context.updated_class)
    assert current == context.updated_value, (
        f"Limiar não foi atualizado: esperado {context.updated_value}, "
        f"obtido: {current}"
    )
    assert context.threshold_mgr.is_running(), \
        "ThresholdManager deve permanecer em execução após atualização de limiar"
