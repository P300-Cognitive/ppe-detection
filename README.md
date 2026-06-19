# PPE Detection

Detector de EPI (Equipamento de Proteção Individual) em tempo real via câmera, usando **YOLO** e **Spec-Driven Design**.

## Spec-Driven Design

Este projeto segue SDD: toda funcionalidade nasce de specs formais antes do código.

```
histories.md → specs/features/ → specs/contracts/ → src/ → tests/spec/
```

Documentação completa: [`specs/README.md`](specs/README.md)

| Documento | Conteúdo |
|-----------|----------|
| [`specs/manifest.yaml`](specs/manifest.yaml) | Rastreabilidade US → spec → teste → código |
| [`specs/constitution.md`](specs/constitution.md) | Princípios do projeto |
| [`specs/architecture.md`](specs/architecture.md) | Pipeline e camadas |
| [`specs/contracts/`](specs/contracts/) | Contratos de interface |
| [`specs/features/`](specs/features/) | Cenários de aceitação por épico |

## Quick start

```bash
# Criar ambiente e instalar
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Validar rastreabilidade das specs
python scripts/validate_specs.py

# Rodar testes de aceitação
pytest tests/spec/ -v

# (Opcional) Baixar modelo offline
python scripts/download_model.py

# Executar com webcam USB
ppe-detection --source 0

# Executar com RTSP
ppe-detection --source "rtsp://user:pass@192.168.1.100/stream"

# Apenas capacete obrigatório, salvar evidências
ppe-detection --required-ppe helmet --save-evidence
```

## Arquitetura

```mermaid
flowchart LR
    CAM[CameraPort] --> DET[DetectorPort]
    DET --> ASS[PPEAssociatorPort]
    ASS --> RULE[RulesEnginePort]
    RULE --> REN[RendererPort]
```

Implementações atuais:

| Port | Adapter |
|------|---------|
| `CameraPort` | `camera/capture.py` |
| `DetectorPort` | `detection/detector.py` (YOLO) |
| `PPEAssociatorPort` | `association/matcher.py` |
| `RulesEnginePort` | `rules/safety.py` |
| `RendererPort` | `visualization/renderer.py` |

## Modelo de IA

Padrão: [`Hexmon/vyra-yolo-ppe-detection`](https://huggingface.co/Hexmon/vyra-yolo-ppe-detection) — detecta Person, Hardhat, Safety Vest, Gloves, Goggles, Mask e classes de violação.

YOLO é a escolha recomendada por: velocidade em tempo real, ecossistema maduro (Ultralytics), modelos pré-treinados de EPI disponíveis e tracking integrado (ByteTrack).

## Status das user stories

Consulte [`specs/manifest.yaml`](specs/manifest.yaml):

- **verified** — spec + código + testes (US-001–002, 008–015, 017–019)
- **implemented** — spec + código
- **specified** — pendente (US-016, US-020+)

## Modos de execução

```bash
# Detector single-câmera (modo legado ou subcomando)
ppe-detection run --source 0 --save-evidence

# Dashboard multi-câmera + histórico + relatórios
ppe-detection dashboard --port 8080 --save-evidence
# Acesse: http://localhost:8080/dashboard/
```

## Como adicionar uma feature

1. Atualize `histories.md` e `specs/features/`
2. Defina contrato em `specs/contracts/`
3. Adicione `Protocol` em `src/ppe_detection/contracts/ports.py`
4. Implemente o adapter
5. Escreva teste em `tests/spec/` com `@pytest.mark.spec("US-XXX")`
6. Atualize `specs/manifest.yaml`

## Configuração

Arquivo padrão: [`config/default.yaml`](config/default.yaml)

Principais opções:

```yaml
camera:
  source: "0"              # USB ou RTSP
rules:
  required_ppe: [helmet, vest]
  confirmation_frames: 15  # frames antes de alertar
model:
  confidence: 0.45
```
