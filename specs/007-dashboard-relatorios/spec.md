# Spec 007: Dashboard, histórico e relatórios

**Status:** retroativa | **Histórias:** US-017, US-018, US-019 | **Cenários:** [`features/epic7_dashboard/`](../../features/epic7_dashboard/)

## Contexto

Operadores acompanham as câmeras em um painel único. Responsáveis pela segurança consultam ocorrências passadas, e gestores acompanham indicadores de conformidade. Decisões de segurança podem ser tomadas a partir desses números, então eles precisam ser reais.

## Histórias de usuário

**US-017 – Visualizar câmeras em tempo real.** Como operador, quero acompanhar todas as câmeras em um painel único, para que o monitoramento seja centralizado.

**US-018 – Consultar histórico de ocorrências.** Como responsável pela segurança, quero pesquisar ocorrências passadas, para que possa realizar auditorias.

**US-019 – Gerar relatórios.** Como gestor de segurança, quero visualizar indicadores de conformidade, para que possa acompanhar a evolução da operação.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Exibir várias câmeras ao mesmo tempo | US-017 | Não atendido | O sistema processa e exibe uma câmera. O cenário só conta nomes em uma lista |
| FR-002 | Exibir alertas em tempo real, sem atualização manual | US-017 | Parcial | Atualiza a cada 2 s, mas a lista só cresce: alertas nunca saem do painel |
| FR-003 | Filtrar ocorrências por data | US-018 | Não atendido | Gera erro 500 com dados reais |
| FR-004 | Filtrar ocorrências por câmera | US-018 | Atendido | |
| FR-005 | Filtrar ocorrências por tipo de EPI | US-018 | Não atendido | Gera erro 500 com dados reais |
| FR-006 | Gerar relatório por período | US-019 | Não atendido | O período é só repetido; nenhum dado é consultado |
| FR-007 | Informar a quantidade de infrações | US-019 | Não atendido | Sempre 0 |
| FR-008 | Informar a taxa de conformidade | US-019 | Não atendido | Sempre 100% |
| FR-009 | Exportar para PDF | US-019 | Parcial | O arquivo é gerado e baixado, mas com os valores fixos |
| FR-010 | Exportar para Excel | US-019 | Parcial | Idem |
| FR-011 | Preservar o histórico após reiniciar | Derivado de US-018 | Não atendido | Fica só em memória, e auditoria exige persistência |

## Casos de borda

- Período sem dados: o relatório deve dizer "sem dados", e não 100% de conformidade.
- Data final antes da inicial, ou data inválida: hoje não há validação.
- Muitos registros: a resposta de `/api/history` não é paginada.

## Critérios de sucesso

- O relatório de um período bate com uma contagem independente das ocorrências daquele período.
- Todos os filtros funcionam com dados produzidos pelo fluxo real.
- O histórico continua disponível após reiniciar a aplicação.
- Com N câmeras ativas, o painel exibe N streams e os alertas indicam a câmera de origem.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] Como calcular a taxa de conformidade? A fórmula muda o significado do número: por exemplo, pessoas conformes sobre pessoas observadas, ou tempo conforme sobre tempo observado.
- [NEEDS CLARIFICATION] Quando um alerta deixa de estar ativo no painel: quando o EPI volta, ou quando alguém o reconhece?
- [NEEDS CLARIFICATION] Quantas câmeras simultâneas o sistema precisa suportar, e em qual hardware?
