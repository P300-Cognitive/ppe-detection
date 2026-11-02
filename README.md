# PPE Detection

Sistema de detecção automática de Equipamentos de Proteção Individual (EPIs) em vídeo, construído com visão computacional e arquitetura Spec-Driven Design (BDD).

---

## Visão Geral

O sistema monitora câmeras em tempo real, detecta pessoas e verifica o uso correto de EPIs (capacetes, coletes, óculos, máscaras, luvas e botas). Quando uma não conformidade é identificada, gera alertas visuais, salva evidências e envia notificações automáticas.

```
Câmera → Detecção de Pessoas → Rastreamento → Detecção de EPI
       → Associação Pessoa/EPI → Regras de Segurança → Alertas
       → Evidências (imagem/vídeo) → Notificações (Telegram/e-mail)
       → Dashboard + Histórico + Relatórios
```

---

## Épicos e Histórias de Usuário

| Épico | Escopo | US |
|---|---|---|
| 1 – Captura de Vídeo | Câmera USB e RTSP, FPS mínimo | US-001, US-002 |
| 2 – Detecção de Pessoas | Bounding box, ID temporário | US-003, US-004 |
| 3 – Detecção de EPI | Capacetes, coletes e outros EPIs | US-005 a US-007 |
| 4 – Associação Pessoa/EPI | IoU head/torso region | US-008, US-009 |
| 5 – Regras de Segurança | Limiar de confirmação por câmera | US-010 a US-012 |
| 6 – Alertas e Evidências | Visual, imagem, vídeo, notificações | US-013 a US-016 |
| 7 – Dashboard | Monitoramento em tempo real, histórico, relatórios | US-017 a US-019 |
| 8 – Administração | Câmeras, modelos de IA, limiares | US-020 a US-022 |

---

## Estrutura do Projeto

```
ppe-detection/
├── features/                        # Especificações BDD (Gherkin)
│   ├── epic1_captura_video/
│   ├── epic2_deteccao_pessoas/
│   ├── epic3_deteccao_epi/
│   ├── epic4_associacao_pessoa_epi/
│   ├── epic5_regras_seguranca/
│   ├── epic6_alertas_evidencias/
│   ├── epic7_dashboard/
│   ├── epic8_administracao/
│   ├── steps/                       # Step definitions Python
│   │   ├── shared_steps.py
│   │   ├── steps_epic1_captura_video.py
│   │   └── ... (um arquivo por épico)
│   └── environment.py
├── src/
│   ├── core/models.py               # Data models compartilhados
│   ├── video/
│   │   ├── capture.py               # VideoCapture (USB / RTSP)
│   │   └── processor.py             # FrameProcessor (thread + FPS)
│   ├── detection/
│   │   ├── person.py                # PersonDetector (YOLOv8)
│   │   └── ppe.py                   # PPEDetector (YOLOv8 custom)
│   ├── tracking/tracker.py          # PersonTracker (ByteTrack)
│   ├── association/associator.py    # PPEAssociator (IoU por região corporal)
│   ├── rules/engine.py              # SafetyRulesEngine
│   ├── alerts/
│   │   ├── visual.py                # VisualAlertRenderer
│   │   └── evidence.py              # EvidenceRecorder (JPEG + MP4)
│   ├── notifications/notifier.py    # NotificationService (Telegram + SMTP)
│   ├── dashboard/
│   │   ├── monitor.py               # DashboardMonitor
│   │   ├── state.py                 # AppState (estado compartilhado thread-safe)
│   │   ├── pipeline.py              # CameraPipeline (loop de processamento)
│   │   └── app.py                   # Flask app factory + rotas REST + HTML
│   ├── reports/
│   │   ├── history.py               # IncidentHistory
│   │   └── generator.py             # ReportGenerator (PDF + Excel)
│   └── admin/
│       ├── camera_manager.py        # CameraManager
│       ├── model_manager.py         # ModelManager (hot-swap)
│       └── threshold_manager.py     # ThresholdManager (hot-reload)
├── tests/fixtures/                  # Fixtures para testes BDD
├── evidence/                        # Imagens e vídeos de ocorrências (gerado)
├── reports/                         # Relatórios PDF e Excel (gerado)
├── models/                          # Modelos de IA carregados (gerado)
├── main.py                          # Ponto de entrada CLI + dashboard web
├── histories.md                     # Histórias de usuário originais
├── requirements.txt
└── pyproject.toml
```

---

## Requisitos

- Python 3.10+
- CUDA (opcional, recomendado para inferência em tempo real)

---

## Instalação

```bash
git clone https://github.com/seu-usuario/ppe-detection.git
cd ppe-detection
pip install -r requirements.txt
```

---

## Configuração

Crie um arquivo `.env` na raiz do projeto com as variáveis necessárias:

```env
# Notificações Telegram
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Notificações E-mail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASS=sua_senha_de_app
EMAIL_TO=destinatario@email.com
```

> Sem essas variáveis, o sistema opera normalmente mas as notificações são desabilitadas.

---

## Como Executar

### Início rápido — câmera USB + dashboard

```bash
python main.py
```

Acesse **http://localhost:5000** no navegador.

### Câmera RTSP com modelo EPI

```bash
python main.py \
  --camera rtsp://192.168.1.10/live \
  --ppe-model models/ppe.pt \
  --required-ppe helmet vest
```

### Janela OpenCV sem dashboard web

```bash
python main.py --camera 0 --show-window --no-web
```

### Todas as opções

```
python main.py --help

  --camera SRC          Fonte de vídeo: índice USB (0, 1…) ou URL RTSP  [padrão: 0]
  --camera-id ID        Identificador da câmera no sistema               [padrão: CAM-01]
  --ppe-model PATH      Caminho para modelo .pt de EPIs treinado
  --confidence 0-1      Limiar mínimo de confiança das detecções         [padrão: 0.5]
  --required-ppe EPI…   EPIs obrigatórios (ex: helmet vest glasses)      [padrão: helmet vest]
  --confirm-frames N    Quadros consecutivos sem EPI para emitir alerta  [padrão: 5]
  --fps FPS             Taxa mínima de processamento                     [padrão: 15]
  --pre-seconds N       Segundos de vídeo capturados antes do alerta     [padrão: 10]
  --post-seconds N      Segundos de vídeo capturados após o alerta       [padrão: 5]
  --host HOST           Host do dashboard web                            [padrão: 0.0.0.0]
  --port PORT           Porta do dashboard web                           [padrão: 5000]
  --no-web              Desabilita o dashboard web
  --show-window         Exibe janela OpenCV com o vídeo anotado
```

> Sem `--ppe-model`, o sistema detecta e rastreia pessoas mas não verifica EPIs — útil para testar câmera e dashboard.

---

## Dashboard Web

O dashboard roda em `http://localhost:5000` e oferece quatro abas:

| Aba | Funcionalidade |
|---|---|
| **Histórico** | Tabela de ocorrências com filtros por data, câmera e tipo de EPI |
| **Limiares** | Sliders por classe de EPI com hot-reload sem reiniciar o sistema |
| **Relatório** | KPIs do período selecionado + download PDF e Excel |
| **Admin** | Cadastro de novas câmeras RTSP |

O painel lateral exibe os alertas ativos em tempo real (atualizado a cada 2 segundos) e o stream de vídeo anotado é servido via MJPEG diretamente no navegador.

### Rotas REST disponíveis

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/video_feed` | Stream MJPEG da câmera anotado |
| `GET` | `/api/alerts` | Alertas ativos (JSON) |
| `GET` | `/api/history` | Histórico com filtros `?date=&camera_id=&ppe_type=` |
| `GET/POST` | `/api/thresholds` | Leitura e atualização de limiares |
| `GET/POST` | `/api/cameras` | Listagem e cadastro de câmeras |
| `GET` | `/api/report` | Relatório JSON por período `?start=&end=` |
| `GET` | `/api/report/pdf` | Download do relatório em PDF |
| `GET` | `/api/report/excel` | Download do relatório em Excel |

---

## Uso via API Python

Para integrar os módulos diretamente em outro código:

### Pipeline manual

```python
from src.video.capture import VideoCapture
from src.tracking.tracker import PersonTracker
from src.detection.ppe import PPEDetector
from src.association.associator import PPEAssociator
from src.rules.engine import SafetyRulesEngine
from src.alerts.visual import VisualAlertRenderer

capture = VideoCapture(source=0)
capture.start()

tracker      = PersonTracker()
ppe_detector = PPEDetector(classes=["helmet", "vest"], model_path="models/ppe.pt")
associator   = PPEAssociator()
engine       = SafetyRulesEngine(camera_id="CAM-01")
renderer     = VisualAlertRenderer()

while capture.is_running():
    frame        = capture.read()
    persons      = tracker.update(frame)
    ppe          = ppe_detector.detect(frame)
    associations = associator.associate(persons, ppe)

    for person in persons:
        if "helmet" not in associations.get(person.track_id, []):
            engine.evaluate(person.track_id, "helmet", threshold=5)
        alert = engine.get_pending_alert(person.track_id)
        if alert:
            frame = renderer.render(frame, [alert])

capture.stop()
```

---

## Modelos de IA

### Detecção de Pessoas

Utiliza `yolov8n.pt` (baixado automaticamente pelo ultralytics na primeira execução). Detecta a classe `person` do dataset COCO.

### Detecção de EPIs

Requer modelo treinado com as classes de EPI. O mapeamento padrão é:

| Índice | Classe |
|--------|--------|
| 0 | helmet |
| 1 | vest |
| 2 | glasses |
| 3 | mask |
| 4 | gloves |
| 5 | boots |

Para usar um modelo customizado:

```python
from src.detection.ppe import PPEDetector

detector = PPEDetector(
    classes=["helmet", "vest"],
    model_path="models/meu_modelo_ppe.pt",
    confidence=0.6,
)
```

Para atualizar o modelo sem reiniciar:

```python
from src.admin.model_manager import ModelManager

manager = ModelManager()
model = manager.upload("models/novo_modelo.pt")
manager.activate(model.id)
```

---

## Administração

### Gerenciar Câmeras

```python
from src.admin.camera_manager import CameraManager

cam_mgr = CameraManager()
camera = cam_mgr.register("rtsp://192.168.1.200/stream")
status = cam_mgr.test_connectivity(camera.rtsp_url)
cam_mgr.disable(camera.id)
```

### Ajustar Limiares de Confiança

```python
from src.admin.threshold_manager import ThresholdManager

th = ThresholdManager()
th.start()
th.set("helmet", 0.75)   # Reduz falsos positivos
th.set("vest", 0.55)     # Aumenta sensibilidade
```

### Configurar Regras por Câmera

```python
from src.rules.engine import SafetyRulesEngine

engine = SafetyRulesEngine(camera_id="CAM-02")
engine.set_required_ppe("CAM-02", ["helmet", "vest"])
```

---

## Relatórios

```python
from src.reports.generator import ReportGenerator

gen = ReportGenerator(output_dir="reports")
report = gen.generate(start="2026-06-01", end="2026-06-30")

pdf_path   = gen.export_pdf(report)    # → reports/report_20260601_20260630.pdf
excel_path = gen.export_excel(report)  # → reports/report_20260601_20260630.xlsx
```

---

## Evidências

Imagens e vídeos são salvos automaticamente em `evidence/`:

```python
from src.alerts.evidence import EvidenceRecorder

recorder = EvidenceRecorder(
    output_dir="evidence",
    pre_alert_seconds=10,
    post_alert_seconds=5,
)

img_path   = recorder.save_image(frame, violation)
video_path = recorder.save_video(violation)
```

---

## Testes BDD

O projeto usa [behave](https://behave.readthedocs.io/) com especificações Gherkin. Cada história de usuário tem seu próprio arquivo `.feature`.

### Executar todos os testes

```bash
python -m behave
```

### Executar por épico

```bash
python -m behave features/epic5_regras_seguranca
python -m behave features/epic6_alertas_evidencias
```

### Dry-run (verificar mapeamento de steps)

```bash
python -m behave --dry-run
```

### Resultado atual

| Épico | Cenários | Status |
|---|---|---|
| 4 – Associação Pessoa/EPI | 4 | ✅ Passando |
| 5 – Regras de Segurança | 8 | ✅ Passando |
| 6 – Alertas e Evidências | 10 | ✅ Passando |
| 7 – Dashboard e Monitoramento | 10 | ✅ Passando |
| 8 – Administração | 9 | ✅ Passando |
| 1–3 – Vídeo, Detecção, Rastreamento | 25 | ⚙️ Requer câmera / modelo treinado |

> **Épicos 1–3** executam normalmente com câmera real ou imagens de teste. Em ambiente sem câmera, os steps de `VideoCapture` levantam `ConnectionError` e os de `PersonDetector`/`PPEDetector` retornam detecções vazias em frames pretos.

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `PPE_TEST_MODE` | Simula envios de notificação (sem rede) | `1` em testes BDD |
| `TELEGRAM_BOT_TOKEN` | Token do bot Telegram | — |
| `TELEGRAM_CHAT_ID` | ID do canal/grupo Telegram | — |
| `EMAIL_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `EMAIL_PORT` | Porta SMTP | `587` |
| `EMAIL_USER` | Usuário de e-mail | — |
| `EMAIL_PASS` | Senha de app do e-mail | — |
| `EMAIL_TO` | Destinatário dos alertas | — |

---

## Dependências Principais

| Pacote | Finalidade |
|---|---|
| `ultralytics` | YOLOv8 para detecção de pessoas e EPIs |
| `opencv-python` | Captura de vídeo e anotação de frames |
| `supervision` | ByteTrack para rastreamento multi-pessoa |
| `behave` | Framework BDD (testes Gherkin) |
| `flask` + `flask-sqlalchemy` | Dashboard web |
| `sqlalchemy` | Persistência de eventos e histórico |
| `pandas` | Manipulação de dados para relatórios |
| `reportlab` | Exportação de relatórios em PDF |
| `openpyxl` | Exportação de relatórios em Excel |
| `python-telegram-bot` | Notificações via Telegram |
| `pydantic-settings` | Gerenciamento de configuração |

---

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.
