# Spec 002: Detecção e rastreamento de pessoas

**Status:** retroativa | **Histórias:** US-003, US-004 | **Cenários:** [`features/epic2_deteccao_pessoas/`](../../features/epic2_deteccao_pessoas/)

## Contexto

Para verificar o uso de EPI, o sistema precisa saber quem está na cena e reconhecer a mesma pessoa ao longo dos quadros. Isso permite atribuir uma não conformidade a alguém específico e evita gerar alertas repetidos.

## Histórias de usuário

**US-003 – Detectar pessoas na imagem.** Como responsável pela segurança, quero identificar pessoas presentes na cena, para que seja possível verificar o uso de EPIs.

**US-004 – Rastrear pessoas entre quadros.** Como responsável pela segurança, quero acompanhar a mesma pessoa ao longo do vídeo, para que alertas não sejam gerados repetidamente.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Desenhar caixa delimitadora em cada pessoa detectada | US-003 | Atendido | Desenho feito pelo fluxo de produção |
| FR-002 | Detectar também pessoas parcialmente visíveis | US-003 | Não verificado | Depende do modelo; não há imagem de teste |
| FR-003 | Atribuir identificador temporário a cada pessoa | US-003 | Atendido | O identificador vem do rastreador. O cenário o procura na saída do detector, onde ele fica vazio |
| FR-004 | Atribuir ID persistente a cada pessoa | US-004 | Não verificado | Código presente; nenhum teste com pessoa real |
| FR-005 | Manter o ID estável enquanto a pessoa estiver visível | US-004 | Não verificado | Idem |
| FR-006 | Suportar múltiplas pessoas ao mesmo tempo | US-004 | Não verificado | Idem |
| FR-007 | Não gerar alertas repetidos para a mesma pessoa | US-004 | Não atendido | O rastreamento existe, mas as regras não o aproveitam para isso. Ver [005/FR-009](../005-regras-seguranca/spec.md) |

## Casos de borda

- Quadro sem nenhuma pessoa: o rastreador retorna lista vazia e não é atualizado naquele quadro.
- Pessoa sai e volta à cena: pode receber um novo ID, o que reinicia a contagem de confirmação.
- Pessoas que se cruzam: os IDs podem ser trocados.

## Critérios de sucesso

- Em um vídeo de teste com pessoas conhecidas, cada pessoa recebe caixa e um ID distinto.
- Uma pessoa visível sem oclusão mantém o mesmo ID durante toda a sua passagem.
- Os cenários passam com imagens reais, sem depender de câmera.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] Quando a pessoa sai e volta, ela conta como a mesma infração ou como uma nova?
- [NEEDS CLARIFICATION] Qual a meta mínima de acurácia de detecção para o ambiente de operação?
