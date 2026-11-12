# Prova de carga de GPU

Valida as premissas do [capacity.md](../capacity.md) numa GPU local antes da compra dos servidores.

O teste reproduz o pipeline proposto na SRS, não o protótipo atual:

| Etapa | Proposta | No teste |
|---|---|---|
| Decode | Todos os frames do stream (15 fps) | PyAV (CPU, 1 núcleo por stream) ou NVDEC |
| Pessoas + visibilidade | Pose a 5 fps por câmera | `yolov8s-pose` TensorRT, batch dinâmico |
| EPI | Recorte de cada pessoa, 2 avaliações/s | `yolov8s` TensorRT como substituto do modelo de EPI ainda não treinado (mesmo custo) |
| Pré-processamento | Workers fazem letterbox, GPU normaliza | Igual |

## Instalação

Requer Python 3.12, driver NVIDIA recente e GPU com suporte a CUDA 12.8 (Blackwell/RTX 50xx incluso).

```bash
py -3.12 -m venv benchmarks/.venv
benchmarks/.venv/Scripts/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
benchmarks/.venv/Scripts/python -m pip install ultralytics "tensorrt-cu12>=10.8,<11" onnx onnxslim av PyNvVideoCodec nvidia-ml-py psutil
```

Use TensorRT 10.x. No 11, a ultralytics passa pelo NVIDIA ModelOpt, que roda uma inferência de referência em CPU e estourou a RAM (32 GB) na exportação com batch 32.

Na RTX 5080 com TensorRT 10.16, a engine INT8 do `yolov8s` não compila (erro interno do Myelin). O `e2e` usa FP16 automaticamente quando falta a INT8. Nesta GPU, INT8 não trouxe ganho sobre FP16.

## Roteiro

Rodar a partir de `benchmarks/`, com o venv ativo (`.venv\Scripts\activate`).

```bash
# 1. Clipe sintético 1080p H.264 + engines TensorRT FP16 e INT8 (~10–20 min)
python gpu_load_test.py prepare

# 2. Throughput de inferência por batch e estimativa de câmeras por GPU
python gpu_load_test.py infer

# 3. Capacidade de decode: CPU vs NVDEC
python gpu_load_test.py decode --streams 25 50 100

# 4. Ponta a ponta, carga média (2 pessoas por câmera)
python gpu_load_test.py e2e --cams 25 50 75 100 --persons 2

# 5. Ponta a ponta, pico (5 pessoas por câmera)
python gpu_load_test.py e2e --cams 25 50 75 100 --persons 5

# 6. Repetir 4 com decode na GPU
python gpu_load_test.py e2e --cams 50 100 --backend nvdec
```

Com gravações reais da planta, acrescente `--videos <pasta>` em todas as etapas, inclusive no `prepare` (os frames reais também servem de calibração INT8).

## Critério de aprovação (SLO) no e2e

Uma quantidade N de câmeras passa quando, durante a janela medida:

- pose e EPI atingem ao menos 95% da taxa-alvo (N × 5/s e N × pessoas × 2/s);
- a idade p95 do frame, da captura ao resultado, fica abaixo de 1 s;
- o descarte de frames fica abaixo de 1%;
- o decode acompanha o tempo real (atraso máximo menor que 1 s).

Com a confirmação de 20 s da SRS, 1 s de latência é folgado e cabe no RNF-002 (alerta em até 3 s).

## Como ler os resultados

Cada etapa imprime tabelas e grava um JSON em `results/`.

- **infer:** `cameras_70pct` é o número de câmeras que uma GPU igual a esta atende só com inferência, a 70% de uso.
- **decode:** `streams_sustentaveis` mostra quantas câmeras 1080p@15 o decoder aguenta; `vram_delta_mb` mostra quanto o NVDEC ocupa.
- **e2e:** "Maior número de câmeras dentro do SLO" é o número que vale para o capacity. `vram_peak_mb` e `ram_delta_gb` mostram o consumo real de memória.

Para converter para a GPU de produção, use a razão de desempenho entre as placas (a RTX 5080 rende próximo de 2× uma L4 em INT8/FP16) e repita a prova no hardware final, se possível.

## Limitações conhecidas

- O modelo de EPI real ainda não existe; `yolov8s` tem o mesmo custo de um modelo de EPI da classe "s".
- O clipe sintético não tem pessoas reais. As pessoas são simuladas com recortes fixos (`--persons`), o que garante carga constante no estágio de EPI.
- RTSP não é testado; o decode lê arquivos. A rede é dimensionada à parte (cerca de 4 Mbps por câmera).
- Windows e GeForce diferem do servidor Linux com L4/RTX Ada; os números servem para validar a ordem de grandeza.
