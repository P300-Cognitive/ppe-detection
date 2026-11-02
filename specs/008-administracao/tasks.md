# Tarefas 008: Administração

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Implementar `CameraManager`, com cadastro, teste de conexão, habilitar e desabilitar, em `src/admin/camera_manager.py` (FR-001, FR-003 a FR-005)
- [x] T002 Criar rotas e tela para cadastrar e listar câmeras (FR-001)
- [x] T003 Implementar `ModelManager`, com envio, validação por extensão e ativação, em `src/admin/model_manager.py` (FR-006 a FR-008)
- [x] T004 Implementar `ThresholdManager` com validação de faixa em `src/admin/threshold_manager.py` (FR-009)
- [x] T005 Criar rotas e tela de limiares (FR-009)
- [x] T006 Escrever os cenários de US-020 a US-022

## Pendente

### Limiares

- [ ] T007 Aplicar os limiares por classe em `PPEDetector` (FR-009, FR-010, FR-011)
- [ ] T008 Reescrever os cenários de limiares para verificar o efeito na detecção (FR-009 a FR-011)
- [ ] T009 Padronizar os nomes de classe entre cenários, tela e API, conforme o glossário canônico

### Modelos

- [ ] T010 Validar o modelo carregando o arquivo e conferindo as classes (FR-007)
- [ ] T011 Trocar o modelo ativo com segurança no fluxo (FR-008)
- [ ] T012 Criar rotas e tela para enviar, listar e ativar modelos (FR-006, FR-008)
- [ ] T013 Reescrever o cenário de troca de modelo, verificando que a detecção usa o novo (FR-008)
- [ ] T014 Decidir os formatos aceitos (esclarecimento na spec)

### Câmeras

- [ ] T015 Implementar a remoção de câmera, com cenário (FR-002)
- [ ] T016 Validar a URL no cadastro (FR-001)
- [ ] T017 Criar rotas e tela para testar, habilitar, desabilitar e remover câmeras (FR-002 a FR-005)
- [ ] T018 Iniciar e parar o monitoramento conforme o estado da câmera (FR-001, FR-004, FR-005; depende de 009/T012)
- [ ] T019 Medir a latência no teste de conexão, ou remover o campo (FR-003)

### Comum

- [ ] T020 Persistir câmeras, modelos e limiares (FR-001, FR-006, FR-009)
- [ ] T021 Definir quem pode administrar e proteger as rotas (depende de 009/T008)
- [ ] T022 Remover `is_running` de `ModelManager` e `ThresholdManager`
