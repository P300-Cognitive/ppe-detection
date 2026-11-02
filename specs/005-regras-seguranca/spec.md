# Spec 005: Regras de segurança

**Status:** retroativa | **Histórias:** US-010, US-011, US-012 | **Cenários:** [`features/epic5_regras_seguranca/`](../../features/epic5_regras_seguranca/)

## Contexto

As regras decidem quando uma ausência de EPI vira alerta. Elas filtram falhas momentâneas de detecção, evitam alertas repetidos e aplicam a norma de cada local.

## Histórias de usuário

**US-010 – Identificar ausência de capacete.** Como responsável pela segurança, quero ser alertado quando uma pessoa estiver sem capacete, para que riscos sejam reduzidos.

**US-011 – Identificar ausência de colete.** Como responsável pela segurança, quero ser alertado quando uma pessoa estiver sem colete, para que medidas corretivas sejam tomadas.

**US-012 – Configurar regras por ambiente.** Como administrador, quero definir quais EPIs são obrigatórios em cada local, para que o sistema reflita as normas da operação.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Alertar somente após N quadros **consecutivos** de ausência | US-010, US-011 | Parcial | A contagem nunca é zerada, então quadros não consecutivos se acumulam |
| FR-002 | Não alertar antes da confirmação | US-010 | Atendido | Vale até o primeiro alerta daquela pessoa |
| FR-003 | Identificar qual pessoa está em não conformidade | US-010 | Atendido | |
| FR-004 | Registrar evento com pessoa, câmera e horário | US-011 | Parcial | Registrado só em memória; perdido ao reiniciar |
| FR-005 | Definir EPIs obrigatórios por câmera | US-012 | Parcial | Fica guardado, mas o fluxo não consulta. Só é definido por `--required-ppe`, sem interface |
| FR-006 | Câmeras distintas podem ter regras diferentes | US-012 | Não atendido | O fluxo usa uma lista global e opera uma câmera só |
| FR-007 | Exigir uma combinação de vários EPIs | US-012 | Atendido | Pela lista global |
| FR-008 | Tratar separadamente a ausência de cada EPI da mesma pessoa | Derivado | Não atendido | Só um alerta pendente por pessoa. Um EPI ainda não confirmado pode aparecer como motivo |
| FR-009 | Não repetir alertas para a mesma ausência | US-004 | Não atendido | Depois de confirmada, a ausência gera alerta em todo quadro seguinte |

## Casos de borda

- A pessoa coloca o EPI após o alerta: hoje o alerta anterior continua ativo no painel.
- O rastreador muda o ID da pessoa: a contagem reinicia.
- Falta de dois EPIs ao mesmo tempo: cada um precisa de confirmação e alerta próprios.
- Falha de detecção de um único quadro no meio de uma sequência: a contagem consecutiva reinicia, conforme o FR-001.

## Critérios de sucesso

- Ausências intercaladas com quadros conformes nunca geram alerta.
- Uma ausência contínua gera exatamente um alerta e uma ocorrência, até ser encerrada.
- Duas câmeras com regras diferentes geram alertas diferentes.
- Uma mudança de regra vale sem reiniciar.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] Quando uma ocorrência termina: quando o EPI volta, quando a pessoa sai de cena, ou após um tempo?
- [NEEDS CLARIFICATION] Uma ausência longa deve gerar lembretes periódicos? Com qual intervalo?
- [NEEDS CLARIFICATION] A confirmação deve ser por quadros ou por tempo? Por quadros, ela varia conforme o FPS.
