# Plano 005: Regras de segurança

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade |
|---|---|
| [src/rules/engine.py](../../src/rules/engine.py) | `SafetyRulesEngine`: contagem, alertas pendentes, eventos e regras por câmera |
| [src/dashboard/pipeline.py](../../src/dashboard/pipeline.py) | Compara EPIs obrigatórios com os associados e chama o motor |

## Interface

```python
SafetyRulesEngine(camera_id="default")
    .evaluate(person_id, missing_ppe, threshold)
    .get_pending_alert(person_id) -> Alert | None
    .force_alert(person_id, ppe_type)    # usado em testes
    .process_alerts()                    # converte pendentes em eventos e limpa a fila
    .get_recorded_events() -> list[Event]
    .set_required_ppe(camera_id, ppe_list)
    .get_required_ppe(camera_id) -> list[str]
```

## Pontos técnicos relevantes

Todos os comportamentos abaixo foram confirmados por script de verificação ou por leitura direta do código.

- **Contagem sem reset:** `evaluate` só é chamado quando o EPI falta e não há método para zerar a contagem. Cinco ausências espalhadas ao longo de horas contam como cinco quadros consecutivos.
- **Alerta a cada quadro:** depois do limiar, cada `evaluate` recria o alerta pendente, e o fluxo gera evidência, notificação e registro no histórico a cada quadro. Isso provavelmente explica as cerca de 23 mil imagens de 2026-06-19 em `evidence/`.
- **Uma pendência por pessoa:** `_pending_alerts` é indexado só por pessoa, então o último EPI confirmado sobrescreve o anterior.
- **Motivo incorreto:** o fluxo testa `get_pending_alert(person)` dentro do laço de cada EPI obrigatório. Com capacete confirmado e colete ainda não confirmado, gera também uma violação "sem vest".
- **Regras não consultadas:** o fluxo lê `state.required_ppe`. Nada de produção chama `get_required_ppe`.
- **Memória sem limite:** contadores e eventos crescem indefinidamente, e nada remove dados de pessoas que saíram.

## Testes

Os 8 cenários passam, mas cobrem menos do que parece:

| Cenário | Limitação |
|---|---|
| Alerta após N quadros | Não testa quadros intercalados nem repetição |
| Registrar evento | Usa `force_alert` e não verifica `ppe_type` |
| Regras por câmera | Apenas lê a configuração; nenhuma avaliação acontece |
| Configurar câmera | Usa `capacete`, enquanto o fluxo usa `helmet` |

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Violado: os cenários de regras por câmera não avaliam conformidade |
| III. Estado honesto | Violado: as regras por câmera não têm efeito em produção |
| IX. Configuração sem reinício | Violado: não há como mudar regras em execução |
| Glossário canônico | Violado: mistura `capacete` e `helmet` |

## Direção proposta

Modelar o estado por `(pessoa, EPI)`, com uma pequena máquina de estados:

```text
CONFORME --(ausência)--> CONTANDO --(N consecutivos)--> ALERTADO --(EPI volta ou pessoa sai)--> CONFORME
             ^                |
             +--(EPI visto)---+
```

- O alerta nasce só na transição para `ALERTADO`, o que resolve a repetição.
- Mover para o motor a avaliação que hoje está no fluxo: `evaluate(camera_id, person_id, epis_associados)` retorna os alertas novos.
- Remover estados de pessoas que não aparecem há algum tempo.
- Persistir os eventos junto com o histórico (ver [spec 007](../007-dashboard-relatorios/plan.md)).
