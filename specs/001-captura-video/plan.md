# Plano 001: Captura e processamento de vídeo

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade |
|---|---|
| [src/video/capture.py](../../src/video/capture.py) | `VideoCapture`: abre USB (índice inteiro) ou RTSP (URL) com `cv2.VideoCapture`. Gera `ConnectionError` em caso de falha |
| [src/video/processor.py](../../src/video/processor.py) | `FrameProcessor`: laço em thread própria com callback por quadro e medição de FPS. **Não é usado em produção** |
| [src/dashboard/pipeline.py](../../src/dashboard/pipeline.py) | `CameraPipeline.run`: o laço realmente usado em produção |

## Interface

```python
VideoCapture(source: int | str)
    .start()         # gera ConnectionError
    .stop()
    .is_running() -> bool
    .read() -> np.ndarray | None   # None indica quadro perdido; gera RuntimeError se não iniciada

FrameProcessor(source=None, min_fps=15)
    .start() / .stop() / .is_running()
    .set_min_fps(fps) / .on_frame(callback) / .get_current_fps()
    .simulate_frame_drop(count)    # stub sem efeito
```

## Pontos técnicos relevantes

- **Dois laços de vídeo:** `FrameProcessor` e `CameraPipeline.run` fazem a mesma coisa, mas só o segundo roda em produção. Os cenários da US-002 testam o primeiro, portanto não cobrem o código real.
- **FPS funciona como teto:** os dois laços dormem o tempo restante até `1 / min_fps`. Isso limita a taxa máxima e não faz nada quando o processamento é lento.
- **Medição de FPS enganosa:** `get_current_fps` devolve o próprio mínimo configurado enquanto houver menos de 2 amostras. O cenário de FPS lê o valor logo após o início e por isso sempre passa.
- **Falha de conexão:** `CameraPipeline.run` captura `ConnectionError`, imprime e encerra a thread, sem deixar nada no `AppState` que o dashboard possa exibir.
- **Quadros `None`:** o laço de produção espera 10 ms e tenta de novo, indefinidamente.

## Testes

| Cenário | Resultado | Motivo |
|---|---|---|
| Câmera USB com sucesso | Passa | Depende de haver uma webcam na máquina |
| RTSP com sucesso | Erro | Espera servidor em `rtsp://localhost:8554/test`, que não existe na suíte |
| USB indisponível, RTSP inacessível | Passam | Testam o erro real |
| US-002 (3 cenários) | Passam | Exercitam `FrameProcessor` sem fonte de vídeo; não comprovam o requisito |

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Violado: cenários de FPS e de perda de quadros não exercitam o comportamento |
| III. Estado honesto | Violado: `simulate_frame_drop` é stub e `FrameProcessor` não tem chamador em produção |
| IV. Falha visível | Violado: falha de conexão fica só no console |
| VIII. Módulos coesos | Violado: há duas implementações do laço |

## Direção proposta

1. Fazer `CameraPipeline` usar um único laço, eliminando a duplicação.
2. Publicar o estado de cada câmera no `AppState` (conectando, ativa, offline, FPS medido).
3. Adicionar reconexão com espera crescente.
4. Testar com um arquivo de vídeo como fonte, sem depender de webcam ou de servidor RTSP.
