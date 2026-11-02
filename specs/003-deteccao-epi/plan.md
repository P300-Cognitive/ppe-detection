# Plano 003: Detecção de EPI

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade |
|---|---|
| [src/detection/ppe.py](../../src/detection/ppe.py) | `PPEDetector`: YOLOv8 com modelo customizado e `render` para anotar o quadro |
| [src/dashboard/pipeline.py](../../src/dashboard/pipeline.py) | Desenha os EPIs com nome e confiança. Não usa `render` |

Mapeamento padrão de classes, que deve coincidir com o modelo treinado:

| Índice | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Classe | `helmet` | `vest` | `glasses` | `mask` | `gloves` | `boots` |

## Interface

```python
PPEDetector(classes, model_path=None, confidence=0.5, class_labels=None)
    .detect(frame) -> list[Detection]   # lista vazia se não houver modelo
    .render(frame, detections) -> np.ndarray
```

## Pontos técnicos relevantes

- **Sem modelo treinado:** os arquivos em `models/` têm 4 bytes e são cópias dos fixtures de teste. O caminho `models/ppe.pt`, citado no README, não existe.
- **Limiar único:** `confidence` vale para todas as classes. Os limiares por classe da [spec 008](../008-administracao/spec.md) não chegam aqui.
- **Classes fixas na inicialização:** a lista vem de `required_ppe` e o modelo é carregado uma única vez, no início do fluxo.
- **Desenho duplicado:** `render` e o fluxo de produção desenham os EPIs separadamente, com cores e formatos diferentes.

## Testes

Todos os 12 cenários falham, por três motivos:

| Problema | Cenários afetados |
|---|---|
| `_ppe_detector` cria o detector sem modelo, então `detect` sempre retorna lista vazia | Todos |
| `mock_frame()` é um quadro preto | Todos |
| O step compara a classe com `"óculos"`, `"máscara"`, `"luvas"` e `"botas"`, mas o detector retorna `glasses`, `mask`, `gloves` e `boots`. Falharia mesmo com modelo e imagem reais | 4 cenários da US-007 |

Além disso, "Associar colete à pessoa correta" só conta os coletes detectados, sem verificar a associação, e "Informar lista de EPIs" só verifica que o atributo `person_id` existe.

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Violado: os cenários não têm modelo nem dados, e há divergência de nomes |
| IV. Falha visível | Violado: a ausência de modelo é silenciosa no detector |
| Glossário canônico | Violado: cenários em português comparados a classes em inglês sem conversão |

## Direção proposta

1. Obter um modelo e registrar sua origem e métricas.
2. Adicionar um modelo pequeno de teste e imagens de cada classe, com uso permitido.
3. Converter os nomes dos EPIs nos steps usando o glossário da constituição.
4. Unificar o desenho em um único módulo.
