# Tarefas 001: Captura e processamento de vídeo

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Implementar `VideoCapture` para USB e RTSP em `src/video/capture.py` (FR-001, FR-002)
- [x] T002 Gerar `ConnectionError` quando a câmera não abre (FR-004)
- [x] T003 Implementar `FrameProcessor` em `src/video/processor.py` (FR-005)
- [x] T004 Iniciar o processamento automaticamente em `CameraPipeline.run` (FR-005)
- [x] T005 Publicar o vídeo anotado para o dashboard e para a janela local (FR-003)
- [x] T006 Ignorar quadros perdidos no laço de produção (FR-007)
- [x] T007 Escrever os cenários de US-001 e US-002

## Pendente

- [ ] T008 Exibir a falha de conexão no dashboard, com estado por câmera em `AppState` (FR-004)
- [ ] T009 Decidir a política de FPS abaixo do mínimo (FR-006, esclarecimento na spec)
- [ ] T010 Medir o FPS real no laço de produção e sinalizar degradação (FR-006)
- [ ] T011 Decidir e implementar a reconexão automática (FR-007, esclarecimento na spec)
- [ ] T012 Unificar `FrameProcessor` e `CameraPipeline.run` em um único laço
- [ ] T013 Remover `simulate_frame_drop` e testar perda de quadros de verdade (FR-007)
- [ ] T014 Corrigir o retorno de `get_current_fps` para não devolver o mínimo sem medição (FR-006)
- [ ] T015 Reescrever os cenários para usar arquivo de vídeo como fonte, sem webcam
- [ ] T016 Marcar com tag o cenário RTSP com sucesso, ou subir um servidor local para ele (FR-002)
