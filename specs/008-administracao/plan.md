# Plano 008: Administração

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade | Exposição |
|---|---|---|
| [src/admin/camera_manager.py](../../src/admin/camera_manager.py) | `CameraManager`: cadastro, listagem, teste de conexão, habilitar e desabilitar | Rotas e tela só para cadastro e listagem |
| [src/admin/model_manager.py](../../src/admin/model_manager.py) | `ModelManager`: envio, validação por extensão, listagem e ativação | Nenhuma |
| [src/admin/threshold_manager.py](../../src/admin/threshold_manager.py) | `ThresholdManager`: limiar por classe, padrão 0,5 | Rotas e tela com controles deslizantes |

## Interface

```python
CameraManager()
    .register(rtsp_url) -> Camera
    .get(id) / .list_all() / .list_enabled()
    .test_connectivity(rtsp_url) -> ConnectivityStatus
    .enable(id) / .disable(id)

ModelManager(models_dir="models")
    .upload(file_path) -> AIModel     # gera FileNotFoundError ou ValueError
    .list_available() / .activate(id) / .get_active()

ThresholdManager()
    .set(ppe_class, value)            # gera ValueError fora de 0..1
    .get(ppe_class) / .get_all() / .remove(ppe_class)
```

## Pontos técnicos relevantes

- **Gerentes desconectados:** em `src/`, os gerentes são usados só pelas rotas de `app.py`. O fluxo não consulta nenhum deles, o que explica a maior parte dos itens não atendidos.
- **Limiares por classe sem efeito:** `PPEDetector` recebe um único `confidence` na criação. O YOLO filtra por esse valor antes de qualquer outro filtro por classe. Portanto, o `conf` do modelo precisa ser igual ao menor limiar configurado, com um filtro por classe depois.
- **Modelo fixo:** `PPEDetector` é criado uma vez, em `CameraPipeline.run`.
- **Validação fraca:** só a extensão é verificada. A aceitação do `.pt` de 4 bytes foi confirmada: é o que os testes usam.
- **Estado em memória:** câmeras, modelos e limiares somem ao reiniciar. Arquivos em `models/` continuam no disco, mas ficam sem registro.
- **`is_running` sem significado:** em `ModelManager` e `ThresholdManager`, é apenas um campo. Não há processo por trás dele, e os cenários o usam para dizer que "o sistema continua rodando".
- **Latência:** o campo `latency_ms` de `ConnectivityStatus` nunca é preenchido.

## Testes

Os 10 cenários passam, mas verificam apenas o estado dos gerentes:

| Cenário | Limitação |
|---|---|
| Habilitar ou desabilitar câmera | Verifica um campo; nenhum fluxo inicia ou para |
| Testar conectividade | Só exige que um status seja retornado |
| Trocar modelo | Verifica `get_active` e `is_running`, sem nenhuma detecção |
| Limiares | Lê de volta o valor gravado, sem nenhuma detecção |

Os cenários usam `capacete`, enquanto a tela usa `helmet`. Eles também gravam arquivos na pasta real `models/` (ver [009/FR-009](../009-orquestracao-plataforma/spec.md)).

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Violado: nenhum cenário verifica efeito na detecção |
| III. Estado honesto | Violado: a tela de limiares sugere um efeito que não existe |
| VI. Privacidade | Violado: rotas administrativas sem autenticação |
| IX. Configuração sem reinício | Violado: nada chega à detecção |
| Glossário canônico | Violado: mistura `capacete` e `helmet` |

## Direção proposta

1. **Limiares reais:** `PPEDetector` recebe o `ThresholdManager`, chama o YOLO com o menor limiar e filtra por classe depois.
2. **Troca de modelo segura:** carregar e validar o novo modelo em segundo plano, testar as classes e só então trocar a referência entre dois quadros. Em caso de falha, manter o modelo anterior.
3. **Supervisor de câmeras:** um componente que observa o `CameraManager` e inicia ou para fluxos (ver [009](../009-orquestracao-plataforma/plan.md)).
4. **Persistência:** guardar as configurações no mesmo banco de dados das ocorrências.
5. **Validação de modelo:** tentar carregar o arquivo e conferir as classes.
6. **API completa:** rotas e telas para todas as operações, protegidas por autenticação.
