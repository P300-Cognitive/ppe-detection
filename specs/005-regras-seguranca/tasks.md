# Tarefas 005: Regras de segurança

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Implementar a contagem e o limiar configurável em `src/rules/engine.py` (FR-002)
- [x] T002 Identificar a pessoa e o EPI no alerta (FR-003)
- [x] T003 Converter alertas em eventos com pessoa, câmera e horário, em memória (FR-004)
- [x] T004 Guardar regras por câmera no motor (FR-005)
- [x] T005 Exigir vários EPIs a partir da lista global `--required-ppe` (FR-007)
- [x] T006 Escrever os cenários de US-010, US-011 e US-012

## Pendente

- [ ] T007 Decidir o fim da ocorrência, os lembretes e a confirmação por quadros ou tempo (esclarecimentos na spec)
- [ ] T008 Zerar a contagem quando o EPI é visto, com cenário de quadros intercalados (FR-001)
- [ ] T009 Indexar o estado por pessoa e EPI, com alerta próprio para cada ausência (FR-008)
- [ ] T010 Emitir o alerta só na transição de estado, com cenário de não repetição (FR-009, 002/FR-007)
- [ ] T011 Corrigir o motivo incorreto gerado no laço do fluxo (FR-008)
- [ ] T012 Mover a avaliação de conformidade do fluxo para o motor
- [ ] T013 Consultar as regras por câmera em produção (FR-005, FR-006)
- [ ] T014 Criar interface e rota para editar regras em execução (FR-005)
- [ ] T015 Fazer os cenários da US-012 avaliarem conformidade de verdade (FR-005 a FR-007)
- [ ] T016 Persistir os eventos (FR-004, 007/T009)
- [ ] T017 Remover estados de pessoas que saíram de cena
- [ ] T018 Padronizar os nomes de EPI nos cenários usando o glossário canônico
