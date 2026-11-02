# Tarefas 006: Alertas e evidências

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Destacar a pessoa e o motivo em vermelho no fluxo de produção (FR-001, FR-002)
- [x] T002 Implementar `VisualAlertRenderer` em `src/alerts/visual.py` (ainda sem uso em produção)
- [x] T003 Salvar imagem com data e hora em `src/alerts/evidence.py` (FR-003, FR-004)
- [x] T004 Criar a estrutura de `save_video` e os parâmetros `--pre-seconds` e `--post-seconds`; o conteúdo ainda é simulado (FR-005)
- [x] T005 Implementar o envio por Telegram (FR-006)
- [x] T006 Implementar o envio por e-mail com anexo (FR-007, FR-008)
- [x] T007 Escrever os cenários de US-013 a US-016

## Pendente

- [ ] T008 Implementar o buffer circular de quadros por câmera (FR-005)
- [ ] T009 Gravar vídeo com quadros reais antes e depois do alerta e chamar a gravação no fluxo (FR-005)
- [ ] T010 Reescrever os cenários de vídeo para verificar a duração e o conteúdo do arquivo (FR-005)
- [ ] T011 Gerar uma imagem e uma notificação por ocorrência, e não por quadro (FR-003, FR-009; depende de 005/T010)
- [ ] T012 Mover gravações e notificações para um trabalhador em segundo plano
- [ ] T013 Verificar a resposta do Telegram e definir timeouts nos dois canais (FR-006, FR-007)
- [ ] T014 Registrar falhas de envio e exibi-las ao operador (FR-006, FR-007)
- [ ] T015 Indicar imagem anexada somente quando o arquivo foi enviado (FR-008)
- [ ] T016 Verificar o resultado de `cv2.imwrite` e tratar falta de espaço em disco (FR-003)
- [ ] T017 Substituir `PPE_TEST_MODE` por testes com servidor local falso (FR-006 a FR-008)
- [ ] T018 Fazer o fluxo usar `VisualAlertRenderer` e testar os pixels do quadro (FR-001, FR-002)
- [ ] T019 Verificar a data e a hora na imagem salva, e não só nos metadados (FR-004)
- [ ] T020 Traduzir o motivo exibido usando o glossário canônico (FR-002)
- [ ] T021 Decidir retenção, conteúdo da imagem e destinatários (esclarecimentos na spec)
- [ ] T022 Implementar a limpeza automática de evidências vencidas (FR-010)
