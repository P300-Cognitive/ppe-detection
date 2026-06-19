# Constituição do Projeto

Princípios que **não devem ser violados** sem revisão explícita da spec.

## 1. Spec primeiro, código depois

Nenhuma funcionalidade entra em `src/` sem spec correspondente em `specs/features/` e entrada em `specs/manifest.yaml`.

## 2. Contratos explícitos

Módulos se comunicam via interfaces definidas em `specs/contracts/` e implementadas como `Protocol` em `src/ppe_detection/contracts/ports.py`. Implementações concretas (YOLO, OpenCV) ficam isoladas nos adapters.

## 3. Domínio independente de IA

Modelos de domínio (`BoundingBox`, `FrameDetections`, `PersonCompliance`) não dependem de Ultralytics, OpenCV ou qualquer framework de ML.

## 4. Configuração externa

Comportamento variável (EPIs obrigatórios, limiares, fontes de câmera) vem de `config/*.yaml`, nunca hardcoded.

## 5. Rastreabilidade total

Todo teste de aceitação referencia pelo menos um ID de spec (`US-xxx` ou `AC-xxx-xxx`).

## 6. Detecção local-first

Inferência roda localmente por padrão. Modelos são referenciados por path ou URI configurável (US-021).

## 7. Falha graciosa

Perda de câmera, quadros ou modelo não derruba o processo — reconexão e logging (US-001, US-002).

## 8. Confirmação antes de alertar

Alertas de não conformidade exigem N frames consecutivos configuráveis para reduzir falsos positivos (US-010, US-011).
