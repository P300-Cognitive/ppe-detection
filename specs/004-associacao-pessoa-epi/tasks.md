# Tarefas 004: Associação entre pessoa e EPI

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Implementar `PPEAssociator` com IoU por região em `src/association/associator.py` (FR-001 a FR-004)
- [x] T002 Definir as regiões de cabeça e tronco (FR-001, FR-003)
- [x] T003 Usar a associação no fluxo de produção (FR-001 a FR-004)
- [x] T004 Escrever os cenários de US-008 e US-009

## Pendente

- [ ] T005 Trocar IoU por fração da área do EPI dentro da região (FR-001 a FR-005)
- [ ] T006 Definir as regiões de `glasses`, `mask`, `gloves` e `boots` (FR-005)
- [ ] T007 Calibrar o limite de associação com imagens reais (FR-001 a FR-005)
- [ ] T008 Adicionar cenários de associação para os quatro EPIs restantes (FR-005)
- [ ] T009 Adicionar cenários com pessoas sobrepostas e com EPI fora do corpo (FR-002, FR-004)
- [ ] T010 Usar `TrackedPerson` e `Detection` nos steps, no lugar de `SimpleNamespace`
