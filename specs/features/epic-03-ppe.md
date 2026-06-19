# Épico 3 — Detecção de EPI

## US-005 — Detectar capacetes {#us-005}

**Contrato**: `specs/contracts/detector.yaml`

- Labels configuráveis: `classes.helmet` (padrão: `Hardhat`).
- Retorna bbox + confidence em `FrameDetections.ppe_items`.

## US-006 — Detectar coletes refletivos {#us-006}

- Labels: `classes.vest` (padrão: `Safety Vest`).
- Associação à pessoa via PPEAssociatorPort (Épico 4).

## US-007 — Detectar outros EPIs {#us-007}

- Labels: `gloves`, `goggles`, `mask`, `boots` em config.
- Cada EPI identificado individualmente pelo label.

## Modelo de IA {#modelo}

**Padrão**: `hf://Hexmon/vyra-yolo-ppe-detection/best.pt`

Classes do modelo:
Person, Hardhat, Safety Vest, Gloves, Goggles, Mask, NO-Hardhat, NO-Safety Vest, ...

Download offline: `python scripts/download_model.py`
