# Tarefas 007: Dashboard, histórico e relatórios

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Criar o app Flask com página única e abas em `src/dashboard/app.py`
- [x] T002 Servir o stream MJPEG em `/video_feed` para uma câmera
- [x] T003 Exibir alertas com atualização a cada 2 s (FR-002)
- [x] T004 Criar a rota e a tela de histórico, com filtro por câmera funcionando (FR-004)
- [x] T005 Criar `AppState` para compartilhar dados entre o fluxo e o Flask
- [x] T006 Criar a exportação de PDF e Excel com download; o conteúdo ainda é fixo (FR-009, FR-010)
- [x] T007 Escrever os cenários de US-017 a US-019

## Pendente

- [ ] T008 Criar o modelo único de ocorrência em `src/core/models.py` (FR-003, FR-005)
- [ ] T009 Persistir as ocorrências em banco de dados (FR-011, 005/FR-004)
- [ ] T010 Corrigir os filtros por data e por EPI usando o modelo real (FR-003, FR-005)
- [ ] T011 Reescrever os cenários de filtro com o modelo real, exigindo resultado não vazio (FR-003 a FR-005)
- [ ] T012 Decidir a fórmula da taxa de conformidade (esclarecimento na spec)
- [ ] T013 **Urgente:** exibir "indisponível" no lugar dos valores fixos do relatório, inclusive em PDF e Excel (FR-007 a FR-010)
- [ ] T014 Calcular os indicadores a partir do histórico, no período pedido (FR-006 a FR-008)
- [ ] T015 Reescrever os cenários de relatório comparando com valores conhecidos, inclusive no arquivo exportado (FR-006 a FR-010)
- [ ] T016 Validar datas nas rotas de histórico e de relatório
- [ ] T017 Paginar `/api/history`
- [ ] T018 Definir quando um alerta sai do painel e implementar (FR-002, esclarecimento na spec)
- [ ] T019 Rodar um fluxo por câmera, com stream e quadro por câmera (FR-001, depende de 009/T012)
- [ ] T020 Exibir todos os streams no painel (FR-001)
- [ ] T021 Testar as rotas com o cliente de testes do Flask
- [ ] T022 Mover a página para arquivos em `templates/` e `static/`
