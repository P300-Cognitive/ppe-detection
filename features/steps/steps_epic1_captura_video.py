"""Step definitions – Épico 1: Captura e Processamento de Vídeo (US-001, US-002)."""
from behave import given, when, then

try:
    from src.video.capture import VideoCapture
except ImportError:
    VideoCapture = None

try:
    from src.video.processor import FrameProcessor
except ImportError:
    FrameProcessor = None


# ── US-001: Capturar vídeo de uma câmera ──────────────────────────────────

@given('que uma câmera USB está conectada à porta do sistema')
def step_usb_connected(context):
    context.camera_source = 0          # índice USB padrão
    context.camera_type = 'usb'

@given('que uma URL de stream RTSP válida está configurada')
def step_rtsp_valid(context):
    context.camera_source = 'rtsp://localhost:8554/test'
    context.camera_type = 'rtsp'

@given('que nenhuma câmera USB está conectada ao sistema')
def step_usb_unavailable(context):
    context.camera_source = 99         # índice de dispositivo inexistente
    context.camera_type = 'usb'

@given('que a URL de stream RTSP está inacessível')
def step_rtsp_unavailable(context):
    context.camera_source = 'rtsp://host-invalido.local/stream'
    context.camera_type = 'rtsp'

@when('o operador inicia a captura de vídeo')
def step_start_capture(context):
    assert VideoCapture is not None, \
        "Implemente src.video.capture.VideoCapture"
    context.capture = VideoCapture(context.camera_source)
    context.capture.start()
    context.capture_error = None

@when('o operador tenta iniciar a captura de vídeo')
def step_try_capture(context):
    assert VideoCapture is not None, \
        "Implemente src.video.capture.VideoCapture"
    try:
        context.capture = VideoCapture(context.camera_source)
        context.capture.start()
        context.capture_error = None
    except Exception as exc:
        context.capture = None
        context.capture_error = str(exc)

@then('o sistema exibe o vídeo em tempo real')
def step_video_realtime(context):
    assert context.capture_error is None, \
        f"Erro inesperado na captura: {context.capture_error}"
    assert context.capture.is_running(), \
        "VideoCapture.is_running() deve retornar True"

@then('o sistema informa falha de conexão com a câmera')
def step_connection_failure(context):
    assert context.capture_error is not None, \
        "O sistema deveria ter registrado erro de conexão mas capture_error está vazio"


# ── US-002: Processar vídeo em tempo real ────────────────────────────────

@given('que a câmera está conectada e exibindo vídeo')
def step_camera_streaming(context):
    assert FrameProcessor is not None, \
        "Implemente src.video.processor.FrameProcessor"
    context.processor = FrameProcessor()
    context.processor_started = False

@given('que o processamento de vídeo está em execução')
def step_processing_running(context):
    assert FrameProcessor is not None, \
        "Implemente src.video.processor.FrameProcessor"
    context.processor = FrameProcessor()
    context.processor.start()

@given('a taxa mínima de FPS está configurada como "{fps}"')
def step_min_fps_set(context, fps):
    context.min_fps = int(fps)
    context.processor.set_min_fps(context.min_fps)

@when('a conexão com a câmera é estabelecida')
def step_camera_connected_event(context):
    context.processor.start()
    context.processor_started = True

@when('os quadros são capturados continuamente')
def step_frames_captured(context):
    context.measured_fps = context.processor.get_current_fps()

@when('ocorre uma pequena perda de quadros no stream')
def step_frame_loss(context):
    context.processor.simulate_frame_drop(count=3)

@then('o processamento de quadros inicia automaticamente sem intervenção manual')
def step_auto_processing_started(context):
    assert context.processor.is_running(), \
        "FrameProcessor.is_running() deve ser True após conexão, sem ação manual"

@then('o sistema mantém pelo menos "{fps}" FPS durante o processamento')
def step_fps_maintained(context, fps):
    assert context.measured_fps >= int(fps), (
        f"FPS medido ({context.measured_fps}) está abaixo do mínimo configurado ({fps})"
    )

@then('o sistema continua processando os quadros seguintes sem interrupção')
def step_processing_continues_after_drop(context):
    assert context.processor.is_running(), \
        "FrameProcessor.is_running() deve permanecer True após queda de quadros"
