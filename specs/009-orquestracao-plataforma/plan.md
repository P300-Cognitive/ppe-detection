# Plano 009: Orquestração e plataforma

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade |
|---|---|
| [main.py](../../main.py) | Linha de comando, criação do estado, thread do fluxo e servidor Flask |
| [src/dashboard/pipeline.py](../../src/dashboard/pipeline.py) | `CameraPipeline`: laço principal que orquestra todos os módulos |
| [src/dashboard/state.py](../../src/dashboard/state.py) | `AppState`: objeto compartilhado entre as threads |
| [src/core/models.py](../../src/core/models.py) | Tipos compartilhados |
| [features/environment.py](../../features/environment.py) | Configuração do behave e `PPE_TEST_MODE=1` |

## Fluxo atual

```text
main.py
  ├─ AppState.setup(...)
  ├─ Thread: CameraPipeline.run()
  │     captura → PersonTracker.update → PPEDetector.detect → PPEAssociator.associate
  │       → SafetyRulesEngine.evaluate → anotação do quadro → AppState.update_frame
  │       → (se houver violação) save_image → push_alert → history.add → notifier.send
  └─ Flask: lê AppState (/video_feed, /api/*)
```

## Opções de linha de comando

| Opção | Padrão |
|---|---|
| `--camera` | `0` |
| `--camera-id` | `CAM-01` |
| `--ppe-model` | nenhum |
| `--confidence` | `0.5` |
| `--required-ppe` | `helmet vest` |
| `--confirm-frames` | `5` |
| `--fps` | `15` |
| `--pre-seconds`, `--post-seconds` | `10`, `5` |
| `--host`, `--port` | `0.0.0.0`, `5000` |
| `--no-web`, `--show-window` | desligados |

## Pontos técnicos relevantes

- **Falsa violação sem modelo:** sem `--ppe-model`, `detect` retorna lista vazia e `required_ppe` continua com o padrão `helmet vest`. Toda pessoa fica sem EPI associado, recebe alerta e gera evidências. É a causa provável das imagens em massa, junto com [005/FR-009](../005-regras-seguranca/spec.md). A mensagem no console diz "apenas rastreamento de pessoas ativo", o que é falso.
- **Thread safety parcial:** `AppState` usa trava apenas para o quadro. Histórico, alertas, limiares e câmeras são lidos e gravados por threads diferentes sem trava.
- **Orquestração no pacote do dashboard:** `CameraPipeline` não depende de Flask, mas fica em `src/dashboard/`.
- **Laço longo:** `CameraPipeline.run` tem cerca de 140 linhas e combina decisão de regras, desenho e efeitos colaterais.
- **Variável sem uso:** `fps_actual` é calculada e nunca é lida.

### Dependências

| Situação | Pacotes |
|---|---|
| Usados e declarados | `behave`, `opencv-python`, `numpy`, `ultralytics`, `supervision`, `openpyxl`, `reportlab`, `flask` |
| Usado sem declaração | `httpx` (hoje disponível só como dependência transitiva) |
| Declarados sem uso | `Pillow`, `pandas`, `sqlalchemy`, `flask-sqlalchemy`, `python-telegram-bot`, `pydantic`, `pydantic-settings` |

### Divergências do README

- Afirma que, sem modelo, o sistema "não verifica EPIs", o que não é verdade.
- Manda criar `.env`, que não é lido.
- Lista o relatório e o vídeo de evidência como funcionais.
- A tabela de testes troca as contagens dos épicos 6 e 8 (são 9 e 10) e diz que os épicos 1 a 3 "requerem câmera ou modelo", sem mencionar que os testes precisam de imagens e têm problemas próprios.
- O `git clone` aponta para `seu-usuario`, e não para `P300-Cognitive`.

### Isolamento de testes

Os steps usam os diretórios padrão (`evidence/`, `models/`, `reports/`), então cada execução deixa arquivos nas pastas reais. A execução de 2026-11-02 fez isso.

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| III. Estado honesto | Violado: mensagem e README sobre execução sem modelo |
| IV. Falha segura | **Violação grave:** sem capacidade de verificar, o sistema declara violação |
| V. Tempo real | Violado: efeitos colaterais no laço |
| VI. Privacidade | **Violação grave:** sem autenticação em `0.0.0.0` |
| X. Dependências enxutas | Violado |

## Direção proposta

1. **Sem modelo:** não avaliar regras e mostrar "EPIs não verificados".
2. **Quebrar o laço:** separar decisão, desenho e efeitos colaterais, deixando o fluxo apenas como coordenador.
3. **Supervisor de câmeras:** iniciar e parar um `CameraPipeline` por câmera habilitada, o que requer `AppState` por câmera.
4. **Segurança:** padrão `127.0.0.1` e autenticação antes de qualquer exposição.
5. **Isolamento:** `before_scenario` usa diretório temporário, passado por parâmetro aos módulos.
6. **Mover** o fluxo para `src/pipeline/`.
