# Tarefas 002: Detecção e rastreamento de pessoas

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Implementar `PersonDetector` com YOLOv8 em `src/detection/person.py` (FR-001, FR-002)
- [x] T002 Implementar `PersonTracker` com ByteTrack em `src/tracking/tracker.py` (FR-003 a FR-006)
- [x] T003 Desenhar caixa e rótulo de ID no fluxo de produção (FR-001, FR-003)
- [x] T004 Escrever os cenários de US-003 e US-004

## Pendente

- [ ] T005 Adicionar imagens e vídeo de teste com pessoas a `tests/fixtures/`, de uso permitido (FR-001, FR-002, FR-004 a FR-006)
- [ ] T006 Trocar `mock_frame()` pelos dados de teste nos steps do épico 2
- [ ] T007 Fazer o cenário de identificador temporário verificar a saída de `PersonTracker` (FR-003)
- [ ] T008 Reescrever o cenário "ID 42" para não exigir um valor específico de ID (FR-005)
- [ ] T009 Medir se ignorar o ByteTrack em quadros vazios afeta os IDs e corrigir, se necessário (FR-005)
- [ ] T010 Decidir como tratar a pessoa que sai e volta à cena (esclarecimento na spec)
- [ ] T011 Definir a meta de acurácia e medi-la em vídeo do ambiente real (esclarecimento na spec)
- [ ] T012 Evitar alertas repetidos usando o ID rastreado (FR-007, implementado em 005/T010)
