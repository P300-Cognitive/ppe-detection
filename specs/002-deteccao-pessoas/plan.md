# Plano 002: Detecção e rastreamento de pessoas

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade |
|---|---|
| [src/detection/person.py](../../src/detection/person.py) | `PersonDetector`: YOLOv8 (`yolov8n.pt`), classe 0 do COCO, confiança padrão 0,5 |
| [src/tracking/tracker.py](../../src/tracking/tracker.py) | `PersonTracker`: combina o detector com ByteTrack (`supervision`) |
| [src/dashboard/pipeline.py](../../src/dashboard/pipeline.py) | Desenha as caixas e os rótulos `P<id>` |

## Interface

```python
PersonDetector(model_path="yolov8n.pt", confidence=0.5)
    .detect(frame) -> list[Detection]        # track_id sempre None

PersonTracker(model_path="yolov8n.pt", confidence=0.5)
    .update(frame) -> list[TrackedPerson]    # track_id e bbox
```

## Pontos técnicos relevantes

- **Pesos do modelo:** `yolov8n.pt` é baixado pelo `ultralytics` na primeira execução e não deve ser versionado.
- **Quadros sem detecção:** `PersonTracker.update` retorna antes de chamar o ByteTrack. O envelhecimento das trilhas perdidas não avança nesses quadros, o que pode afetar a manutenção de IDs. Esse efeito ainda não foi medido.
- **Limiar global:** a confiança de pessoas vem de `--confidence`, o mesmo valor usado para EPIs.

## Testes

Todos os 6 cenários falham, por problemas nos próprios testes:

| Problema | Cenários afetados |
|---|---|
| `mock_frame()` gera um quadro preto, sem pessoas. Os steps têm comentário "substituir por fixture real" | Todos |
| O step procura `track_id` na saída de `PersonDetector`, onde ele é sempre `None`. Com duas ou mais pessoas, os IDs parecem duplicados | Identificador temporário |
| O ByteTrack gera IDs automáticos, então a pessoa nunca receberá o ID "42" exigido | ID estável |

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Violado: os cenários não têm dados capazes de exercitar o comportamento |
| VIII. Módulos coesos | Respeitado: detecção e rastreamento estão separados |

## Direção proposta

1. Adicionar a `tests/fixtures/` imagens e um vídeo curto com pessoas, de uso permitido e sem dados de trabalhadores reais.
2. Fazer o cenário de identificador usar `PersonTracker`.
3. Reescrever o cenário "ID 42" para capturar o ID atribuído e verificar que ele permanece.
