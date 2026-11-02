# Plano 006: Alertas e evidências

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade | Uso em produção |
|---|---|---|
| [src/alerts/visual.py](../../src/alerts/visual.py) | `VisualAlertRenderer`: caixas vermelhas e rótulos | Instanciado, mas nunca chamado |
| [src/dashboard/pipeline.py](../../src/dashboard/pipeline.py) | Desenha as caixas e os motivos diretamente | Sim |
| [src/alerts/evidence.py](../../src/alerts/evidence.py) | `EvidenceRecorder`: `save_image` e `save_video` | Só `save_image` |
| [src/notifications/notifier.py](../../src/notifications/notifier.py) | `NotificationService`: Telegram (`httpx`) e e-mail (SMTP) | Sim |

## Interface

```python
EvidenceRecorder(output_dir="evidence", pre_alert_seconds=10, post_alert_seconds=5)
    .save_image(frame, violation) -> str
    .save_video(violation) -> str

NotificationService(channels)
    .send(violation, image_path=None) -> NotificationResult
```

Credenciais lidas do ambiente: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS` e `EMAIL_TO`. Com `PPE_TEST_MODE=1`, os envios são simulados.

## Pontos técnicos relevantes

- **Vídeo simulado:** `save_video` não recebe quadros. Ele escreve quadros pretos de 640 × 480 e registra nos metadados os segundos configurados. Não há buffer dos quadros anteriores ao alerta. Os arquivos `.mp4` em `evidence/` vêm dos testes.
- **Falso sucesso no Telegram:** `_send_telegram` não verifica a resposta HTTP e retorna `True` mesmo com token inválido.
- **Falso anexo:** `image_attached` é `True` sempre que há caminho e algum envio deu certo, mesmo que o arquivo não exista. O próprio cenário aponta para `tests/fixtures/sample_violation.jpg`, que não existe.
- **Erros descartados:** `except Exception: return False`, sem nenhum registro.
- **Envio bloqueante:** Telegram e SMTP rodam dentro do laço de vídeo. O `httpx.post` usa o timeout padrão da biblioteca, e a conexão SMTP não define timeout.
- **`.env` não é carregado:** o README manda criar o arquivo, mas nenhum código o lê. Ver [spec 009](../009-orquestracao-plataforma/spec.md).
- **Cliente HTTP:** o envio usa `httpx`, que não está em `requirements.txt`. O `python-telegram-bot`, declarado lá, não é usado.

## Testes

Os 9 cenários passam, mas a maioria não comprova o requisito:

| Cenário | Limitação |
|---|---|
| Alerta visual | Testa `VisualAlertRenderer`, que produção não usa, e consulta estado interno, não pixels |
| Imagem com data e hora | Verifica metadados, não a imagem |
| Vídeo pré e pós-alerta | Verifica metadados, não o conteúdo |
| Notificações | `PPE_TEST_MODE` faz tudo retornar `True` |

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Violado: vídeo e notificações não são exercitados |
| III. Estado honesto | Violado: vídeo simulado e sucesso sem confirmação |
| IV. Falha visível | Violado: falhas de envio são descartadas |
| V. Tempo real não bloqueante | Violado: rede e disco no laço de vídeo |
| VI. Privacidade | Violado: sem retenção nem controle de acesso |
| VIII. Módulos coesos | Violado: duas implementações do desenho |

## Direção proposta

1. **Buffer circular por câmera:** guardar os últimos N segundos, e o gravador recebe os quadros reais antes e depois do alerta.
2. **Trabalhador em segundo plano:** uma fila limitada processa gravações e notificações fora do laço de vídeo.
3. **Dispensar um desenho:** fazer o fluxo usar `VisualAlertRenderer`.
4. **Confirmação real:** verificar a resposta HTTP, definir timeouts e registrar as falhas.
5. **Retenção:** tarefa periódica que apaga evidências vencidas.
6. **Testes de notificação:** usar um servidor local falso, em vez de um atalho dentro do código de produção.
