# Spec 006: Alertas e evidências

**Status:** retroativa | **Histórias:** US-013, US-014, US-015, US-016 | **Cenários:** [`features/epic6_alertas_evidencias/`](../../features/epic6_alertas_evidencias/)

## Contexto

Quando uma não conformidade é confirmada, o sistema precisa mostrá-la na tela, guardar evidências para auditoria e avisar as pessoas responsáveis.

## Histórias de usuário

**US-013 – Exibir alerta visual.** Como operador, quero visualizar imediatamente uma não conformidade, para que eu possa agir rapidamente.

**US-014 – Registrar imagem da ocorrência.** Como responsável pela segurança, quero salvar evidências da infração, para que seja possível auditoria posterior.

**US-015 – Registrar vídeo da ocorrência.** Como responsável pela segurança, quero armazenar alguns segundos antes e depois do evento, para que exista contexto da ocorrência.

**US-016 – Enviar notificação automática.** Como responsável pela segurança, quero receber alertas instantâneos, para que possa agir rapidamente.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Destacar em vermelho a pessoa em não conformidade | US-013 | Atendido | Desenhado pelo fluxo. O cenário testa outro módulo, sem uso em produção |
| FR-002 | Exibir o motivo do alerta perto da caixa | US-013 | Parcial | Exibido, mas pode incluir um EPI ainda não confirmado ([005/FR-008](../005-regras-seguranca/spec.md)). Usa o nome em inglês: "SEM HELMET" |
| FR-003 | Salvar imagem da ocorrência em disco | US-014 | Parcial | Salva, mas uma por quadro enquanto durar a ausência |
| FR-004 | Incluir data e hora na imagem | US-014 | Atendido | O cenário só verifica metadados. A imagem não destaca a pessoa infratora |
| FR-005 | Gravar vídeo com N segundos antes e M depois do alerta | US-015 | Não atendido | O arquivo contém só quadros pretos, e o fluxo nunca o grava |
| FR-006 | Notificar por Telegram | US-016 | Parcial | Informa sucesso mesmo se o Telegram recusar o envio. Nunca testado com envio real |
| FR-007 | Notificar por e-mail | US-016 | Parcial | Implementado, nunca testado com envio real. Erros são descartados em silêncio |
| FR-008 | Incluir a imagem da ocorrência na notificação | US-016 | Parcial | Informa imagem anexada mesmo se o arquivo não existir |
| FR-009 | Limitar a quantidade de notificações por ocorrência | Derivado de US-004 | Não atendido | Uma notificação por quadro enquanto durar a ausência |
| FR-010 | Aplicar um prazo de retenção às evidências | Constituição | Não atendido | Os arquivos se acumulam sem limite |

## Casos de borda

- Canal não configurado: a notificação é ignorada, sem aviso ao operador.
- Disco cheio: a gravação falha, e hoje `cv2.imwrite` não tem o resultado verificado.
- Telegram ou e-mail fora do ar: a falha não é registrada, e não há nova tentativa.
- Alerta logo após o início: o trecho anterior ao alerta pode ser menor que o configurado.

## Critérios de sucesso

- Cada ocorrência gera uma imagem, um vídeo com conteúdo real e uma notificação por canal configurado.
- O vídeo mostra a cena nos períodos configurados antes e depois do alerta.
- Uma falha de envio aparece para o operador e fica registrada.
- As evidências respeitam o prazo de retenção.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] Qual o prazo de retenção das evidências, e quem tem acesso a elas? Convém consultar o responsável por privacidade (LGPD).
- [NEEDS CLARIFICATION] A imagem de evidência deve mostrar a anotação da pessoa infratora, ou o quadro original?
- [NEEDS CLARIFICATION] Quem recebe as notificações: destinatário único ou por câmera ou turno?
