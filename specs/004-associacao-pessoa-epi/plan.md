# Plano 004: Associação entre pessoa e EPI

**Spec:** [spec.md](spec.md)

## Implementação atual

[src/association/associator.py](../../src/association/associator.py) contém `PPEAssociator`, que compara cada EPI com a região do corpo esperada, medindo a sobreposição por IoU. O EPI vai para a pessoa de maior IoU, desde que acima de 0,10.

| Classe | Região comparada |
|---|---|
| `helmet` | Cabeça: 30% superiores da caixa da pessoa |
| `vest` | Tronco: faixa de 20% a 70% da altura |
| Demais classes | A caixa inteira da pessoa |

## Interface

```python
PPEAssociator.associate(persons, ppe_detections) -> dict[int, list[str]]
# track_id -> nomes das classes associadas; toda pessoa aparece no resultado
```

## Pontos técnicos relevantes

**O IoU é a métrica errada para objetos pequenos.** Ele penaliza a diferença de tamanho entre as caixas, e os EPIs são bem menores que a caixa inteira da pessoa. O resultado foi verificado em uma pessoa de 200 × 500 pixels:

| EPI | Caixa testada | Associado? |
|---|---|---|
| `helmet` | 60 × 60 | Sim |
| `vest` | 160 × 230 | Sim |
| `glasses` | 40 × 15 | Não |
| `mask` | 50 × 30 | Não |
| `gloves` | 30 × 30 | Não |
| `boots` | 70 × 40 | Não |

O capacete passa por pouco nesse exemplo (IoU de cerca de 0,12), então um capacete menor na imagem também pode não ser associado.

Outros pontos:

- **Sem exclusividade:** um EPI vai para uma pessoa só, mas nada impede uma pessoa de receber vários da mesma classe.
- **Regiões fixas:** as proporções assumem uma pessoa em pé e não valem para alguém agachado ou cortado pelo enquadramento.

## Testes

Os 4 cenários passam, usando caixas sintéticas em `SimpleNamespace`. Eles cobrem só capacete e colete, com pessoas lado a lado e sem sobreposição.

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Parcial: testes bons para o que cobrem, mas com tipos falsos e sem os quatro outros EPIs |
| IV. Falha segura | Violado: exigir `glasses`, por exemplo, gera falsa violação para todos |
| VIII. Módulos coesos | Respeitado |

## Direção proposta

1. Trocar IoU por **fração da área do EPI dentro da região** (interseção dividida pela área do EPI), que não penaliza objetos pequenos.
2. Definir uma região por classe: rosto para `glasses` e `mask`, extremidades para `gloves`, base para `boots`.
3. Validar o novo limite com imagens reais antes de adotá-lo.
