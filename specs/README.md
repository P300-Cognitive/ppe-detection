# Specs do PPE Detection

Documentação retroativa do que foi desenvolvido até o commit `0781945`, escrita para a migração a Spec-Driven Development. As regras do processo estão na [constituição](../memory/constitution.md).

## Situação geral

A suíte tem 66 cenários. Em 2026-11-02, com `python -m behave`, **47 passaram, 18 falharam e 1 deu erro**.

Cenário passando não significa requisito atendido: muitos cenários validam apenas configuração ou metadados. Por isso, cada spec avalia seus requisitos com base no código, de forma independente do resultado dos testes.

| Spec | Histórias | Cenários que passam | Situação |
|---|---|---|---|
| [001 – Captura de vídeo](001-captura-video/spec.md) | US-001, US-002 | 6 de 7 | Captura funciona; FPS mínimo não é garantido |
| [002 – Detecção e rastreamento de pessoas](002-deteccao-pessoas/spec.md) | US-003, US-004 | 0 de 6 | Implementado; testes usam quadro preto |
| [003 – Detecção de EPI](003-deteccao-epi/spec.md) | US-005 a US-007 | 0 de 12 | Código pronto; não há modelo treinado no repositório |
| [004 – Associação pessoa/EPI](004-associacao-pessoa-epi/spec.md) | US-008, US-009 | 4 de 4 | Capacete e colete funcionam; demais EPIs nunca associam |
| [005 – Regras de segurança](005-regras-seguranca/spec.md) | US-010 a US-012 | 8 de 8 | Confirmação não é consecutiva; alertas se repetem |
| [006 – Alertas e evidências](006-alertas-evidencias/spec.md) | US-013 a US-016 | 9 de 9 | Vídeo de evidência é em branco e nunca é gravado pelo fluxo |
| [007 – Dashboard e relatórios](007-dashboard-relatorios/spec.md) | US-017 a US-019 | 10 de 10 | Relatório com valores fixos; filtros quebrados; uma câmera só |
| [008 – Administração](008-administracao/spec.md) | US-020 a US-022 | 10 de 10 | Alterações não chegam à detecção |
| [009 – Orquestração e plataforma](009-orquestracao-plataforma/spec.md) | Sem história | Sem cenários | Fluxo funciona; sem autenticação; testes sujam pastas reais |

## Prioridade sugerida

A ordem abaixo é uma proposta, com os maiores riscos à segurança primeiro.

1. **Relatório falso:** a conformidade sempre aparece como 100%, com 0 infrações ([007](007-dashboard-relatorios/spec.md), FR-006 a FR-010).
2. **Falsa violação sem modelo:** sem `--ppe-model`, toda pessoa é tratada como infratora, ao contrário do que diz o README ([009](009-orquestracao-plataforma/spec.md), FR-005).
3. **Alertas repetidos a cada quadro:** geram evidências e notificações em massa. Há cerca de 23 mil imagens em `evidence/` ([005](005-regras-seguranca/spec.md), FR-009).
4. **Contagem não consecutiva:** a ausência se acumula para sempre, gerando alertas indevidos ([005](005-regras-seguranca/spec.md), FR-001).
5. **Filtros do histórico:** filtrar por data ou por EPI gera erro 500 com dados reais ([007](007-dashboard-relatorios/spec.md), FR-003 e FR-005).
6. **Autenticação:** o dashboard escuta em `0.0.0.0` sem nenhum controle de acesso ([009](009-orquestracao-plataforma/spec.md), FR-008).
7. **Vídeo de evidência:** o arquivo é só de quadros pretos, e o fluxo nunca o grava ([006](006-alertas-evidencias/spec.md), FR-005).
8. **Administração desconectada:** limiares, modelo ativo e regras por câmera não afetam a detecção ([008](008-administracao/spec.md), [005](005-regras-seguranca/spec.md)).
9. **Modelo de EPI:** sem modelo treinado, nada do épico 3 pode ser validado ([003](003-deteccao-epi/spec.md)).

## Como ler os documentos

**Estados de requisito, em `spec.md`:**

| Estado | Significado |
|---|---|
| Atendido | Funciona pelo fluxo de produção |
| Parcial | Parte do requisito funciona, ou existe no módulo mas não está integrada |
| Não atendido | Não funciona, ou o comportamento é simulado |
| Não verificado | O código existe, mas não há como comprovar sem modelo ou dados reais |

**Tarefas, em `tasks.md`:**

- `[x]` significa que o trabalho descrito existe no código.
- `[ ]` significa que o trabalho está pendente.

As avaliações vieram da leitura do código, de um script de verificação pontual e da execução da suíte. O sistema não foi testado de ponta a ponta com câmera e pessoas reais.

## Como criar uma spec nova

1. Crie `specs/NNN-nome-curto/`, seguindo a numeração.
2. Escreva `spec.md` com histórias, requisitos e critérios de sucesso, sem citar tecnologia.
3. Escreva os cenários em `features/`.
4. Escreva `plan.md`, incluindo a verificação contra a constituição.
5. Escreva `tasks.md`, ligando cada tarefa a um `FR-xxx`.
6. Implemente e marque as tarefas conforme a definição de pronto.

## Rastreabilidade

| Épico em `features/` | Spec |
|---|---|
| `epic1_captura_video` | 001 |
| `epic2_deteccao_pessoas` | 002 |
| `epic3_deteccao_epi` | 003 |
| `epic4_associacao_pessoa_epi` | 004 |
| `epic5_regras_seguranca` | 005 |
| `epic6_alertas_evidencias` | 006 |
| `epic7_dashboard` | 007 |
| `epic8_administracao` | 008 |
