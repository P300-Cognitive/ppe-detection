# Spec 009: Orquestração e plataforma

**Status:** retroativa | **Histórias:** nenhuma; registra o que foi construído fora dos épicos | **Cenários:** nenhum

## Contexto

O ponto de entrada, o fluxo que liga as etapas e os aspectos de plataforma foram desenvolvidos sem história de usuário. Eles concentram boa parte da integração do sistema e por isso ganham uma spec própria.

## História de usuário proposta

Como operador, quero iniciar o sistema com um único comando, para que câmera, análise, alertas e dashboard funcionem juntos.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Encadear captura, rastreamento, detecção de EPI, associação, regras, alertas, evidências e notificações | README | Atendido | Com as limitações de cada spec |
| FR-002 | Configurar a execução por linha de comando | README | Atendido | Fonte, modelo, EPIs, confirmação, FPS, evidências, host e porta |
| FR-003 | Permitir executar sem o dashboard web | README | Atendido | `--no-web` |
| FR-004 | Permitir exibir o vídeo em uma janela local | README | Atendido | `--show-window` |
| FR-005 | Sem modelo de EPI, detectar e rastrear pessoas sem verificar EPIs | README | Não atendido | Toda pessoa é tratada como infratora, gerando evidências e notificações falsas |
| FR-006 | Carregar credenciais do arquivo `.env`, como o README orienta | README | Não atendido | Nenhum código lê esse arquivo. Só variáveis de ambiente já definidas funcionam |
| FR-007 | Declarar exatamente as dependências usadas | Constituição | Parcial | `httpx` é usado sem estar declarado, e 7 dependências declaradas não são importadas |
| FR-008 | Exigir autenticação para acessar dashboard, streams e administração | Constituição | Não atendido | Escuta em `0.0.0.0` por padrão, sem nenhum controle de acesso |
| FR-009 | Testes não devem alterar dados reais | Constituição | Não atendido | Cada execução grava em `evidence/`, `models/` e `reports/` |
| FR-010 | Manter artefatos gerados fora do Git | Constituição | Parcial | Não foram versionados, mas não estão no `.gitignore`. Um `git add .` incluiria 1,8 GB |
| FR-011 | Não bloquear o vídeo com rede ou disco | Constituição | Não atendido | Ver [spec 006](../006-alertas-evidencias/plan.md) |
| FR-012 | Executar uma análise por câmera habilitada | US-017, US-020 | Não atendido | Apenas uma câmera, definida na inicialização |
| FR-013 | Manter o README fiel ao sistema | Constituição | Parcial | Ver o plano |

## Casos de borda

- Falha ao carregar o modelo de EPI: hoje a thread do fluxo termina com exceção, enquanto o dashboard continua no ar.
- Encerramento: o `pipeline.stop()` só sinaliza o fim, sem esperar a thread terminar.

## Critérios de sucesso

- Sem modelo de EPI, nenhuma violação é gerada e a interface indica "EPIs não verificados".
- Uma instalação limpa, usando só `requirements.txt`, consegue rodar e enviar notificações.
- Depois de rodar a suíte, `git status` e as pastas de dados continuam como estavam.
- Acessar o dashboard sem credenciais é recusado.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] Em qual ambiente o sistema será implantado (rede local ou exposto), e qual o método de autenticação?
