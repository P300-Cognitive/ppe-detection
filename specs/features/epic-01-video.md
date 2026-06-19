# Épico 1 — Captura e Processamento de Vídeo

## US-001 — Capturar vídeo de uma câmera {#us-001}

**Contrato**: `specs/contracts/camera.yaml`

### Cenários de aceitação

```gherkin
Cenário: AC-001-1 — Aceitar câmera USB por índice
  Dado uma configuração com source "0"
  Quando CameraCapture parseia a source
  Então a source interna deve ser o inteiro 0

Cenário: AC-001-2 — Aceitar stream RTSP
  Dado uma configuração com source "rtsp://192.168.1.1/stream"
  Quando CameraCapture é instanciada
  Então is_rtsp deve ser true

Cenário: AC-001-3 — Falha de conexão informativa
  Dado uma câmera indisponível no índice 99
  Quando connect() é chamado
  Então deve lançar CameraError com mensagem contendo o source
```

---

## US-002 — Processar vídeo em tempo real {#us-002}

**Contrato**: `specs/contracts/camera.yaml`, pipeline em `architecture.md`

### Cenários de aceitação

```gherkin
Cenário: AC-002-1 — Processamento contínuo após conexão
  Dado um CameraCapture conectado
  Quando frames() é iterado
  Então deve produzir frames sem intervenção manual

Cenário: AC-002-2 — Resiliência a perda de quadros
  Dado um frame None retornado por read()
  Quando frames() continua
  Então deve tentar reconectar em vez de encerrar

Cenário: AC-002-3 — FPS mínimo configurável
  Dado min_fps configurado em camera.min_fps
  Quando o pipeline processa frames
  Então deve registrar warning se FPS médio ficar abaixo do mínimo
```
