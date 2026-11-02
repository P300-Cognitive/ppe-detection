# Tarefas 009: Orquestração e plataforma

**Spec:** [spec.md](spec.md) | **Plano:** [plan.md](plan.md)

## Entregue

- [x] T001 Implementar a linha de comando em `main.py` (FR-002)
- [x] T002 Implementar `CameraPipeline`, ligando todas as etapas (FR-001)
- [x] T003 Implementar `AppState` com trava para o quadro
- [x] T004 Permitir execução sem web e com janela local (FR-003, FR-004)
- [x] T005 Configurar behave e `features/environment.py`
- [x] T006 Ler credenciais de variáveis de ambiente

## Pendente

### Urgente

- [ ] T007 **Urgente:** sem modelo, não avaliar regras e exibir "EPIs não verificados", com cenário (FR-005)
- [ ] T008 Decidir o ambiente e o método de autenticação; usar `127.0.0.1` como padrão e proteger as rotas (FR-008)
- [ ] T009 Adicionar `evidence/`, `models/`, `reports/` e `*.pt` ao `.gitignore`, mantendo os fixtures de teste (FR-010)

### Configuração e dependências

- [ ] T010 Carregar o `.env`, ou corrigir o README (FR-006)
- [ ] T011 Declarar `httpx` e remover as dependências sem uso, mantendo as necessárias para 007/T009 (FR-007)

### Orquestração

- [ ] T012 Criar o supervisor de um fluxo por câmera habilitada (FR-012)
- [ ] T013 Tornar `AppState` por câmera, com acesso seguro entre threads (FR-012)
- [ ] T014 Separar decisão, desenho e efeitos colaterais em `CameraPipeline.run` (FR-011)
- [ ] T015 Tratar a falha ao carregar modelos, exibindo-a na interface
- [ ] T016 Esperar a thread terminar no encerramento
- [ ] T017 Mover o fluxo para `src/pipeline/`
- [ ] T018 Adicionar um cenário de ponta a ponta com vídeo de teste (FR-001)

### Testes e documentação

- [ ] T019 Usar diretórios temporários nos testes (FR-009)
- [ ] T020 Separar por tag os cenários que dependem de câmera, modelo ou rede
- [ ] T021 Corrigir as divergências do README listadas no plano (FR-013)
- [ ] T022 Configurar integração contínua para rodar a suíte em cada pull request
