# P300 Vision Safety — Resultados da Prova de Carga (RTX 5080)

**Data:** 10/11/2026
**Objetivo:** validar com medições as premissas do [capacity.md](capacity.md) antes da compra dos servidores.
**Referências:** [P300_Vision_Safety_SRS_v1.0.md](P300_Vision_Safety_SRS_v1.0.md) · roteiro e script em [benchmarks/](benchmarks/README.md)

> **Resumo:** na RTX 5080, uma única GPU atendeu **90 câmeras na carga média** (2 pessoas por câmera) e **60 câmeras no pico** (5 pessoas por câmera) dentro do critério de aprovação. Nas falhas, a GPU estava em só cerca de 49% de uso: **o limite foi o pós-processamento em Python (NMS), não a GPU nem a VRAM.** A aplicação usou cerca de 6,5 GB de VRAM, o que confirma que 24 GB não são necessários.

---

## 1. Ambiente de teste

| Item | Configuração |
|---|---|
| CPU | Intel Core i9-14900KF (24 núcleos, 32 threads) |
| RAM | 32 GB |
| GPU | NVIDIA GeForce RTX 5080 16 GB (driver 617.14) |
| SO | Windows 11 Pro |
| Software | Python 3.12, PyTorch 2.11 (CUDA 12.8), TensorRT 10.16, Ultralytics 8.4, PyAV 19, PyNvVideoCodec 2.2 |
| Vídeo | Clipe sintético 1080p H.264, 4 Mbps, 15 fps, com textura, ruído e objetos em movimento |
| Modelos | `yolov8s-pose` (pessoas e pose) e `yolov8s` (substituto do modelo de EPI, de mesmo custo), TensorRT FP16, batch dinâmico até 32 |

O teste reproduz o pipeline proposto na SRS:

| Etapa | Como foi simulada |
|---|---|
| Decode | Todos os frames do stream a 15 fps (H.264 exige), 1 thread por câmera |
| Pessoas + visibilidade | Pose a 5 fps por câmera |
| EPI | Recorte de cada pessoa, cerca de 2 avaliações por segundo |
| Pré-processamento | Workers fazem o letterbox; a GPU normaliza |

---

## 2. Inferência

Throughput por modelo com batch 32:

| Modelo | Só a rede | Com NMS (ultralytics) |
|---|---|---|
| Pose (`yolov8s-pose`) FP16 | 1.954 img/s (GPU 97%) | 1.397 img/s (GPU 72%) |
| Pose (`yolov8s-pose`) INT8 | 1.880 img/s (GPU 97%) | 1.355 img/s (GPU 72%) |
| EPI (`yolov8s`, 80 classes) FP16 | 2.114 img/s (GPU 97%) | 835 img/s (GPU 44%) |

Câmeras por RTX 5080, só com inferência:

| Cenário | GPU por câmera | Câmeras a 70% de uso | Câmeras a 100% de uso |
|---|---|---|---|
| Só a rede, 2 pessoas por câmera | 4,5 ms | **153** | 219 |
| Só a rede, 5 pessoas por câmera | 7,3 ms | **94** | 135 |
| Com NMS, 2 pessoas por câmera | 8,4 ms | 83 | 119 |
| Com NMS, 5 pessoas por câmera | 15,6 ms | 44 | 64 |

**Conclusões:**
- **O NMS em Python é o gargalo atual.** Com ele, o modelo de EPI cai para cerca de 40% do throughput da rede, e a GPU fica ociosa.
- **INT8 não trouxe ganho nesta GPU.** A pose INT8 foi até um pouco mais lenta que FP16. FP16 é suficiente.

---

## 3. Decode de vídeo

Capacidade sem limite de tempo real:

| Caminho | Streams abertos | Throughput | Câmeras 1080p@15 sustentáveis | CPU | NVDEC | VRAM adicional |
|---|---|---|---|---|---|---|
| CPU (PyAV) | 25 | 2.478 fps | 165 | 91% | — | 0 |
| CPU (PyAV) | 50 | 2.666 fps | 177 | 100% | — | 0 |
| CPU (PyAV) | 100 | 2.633 fps | 175 | 96% | — | 0 |
| NVDEC | 25 | 1.978 fps | 131 | 84% | 39% | 1,9 GB |
| NVDEC | 50 | 2.092 fps | 139 | 85% | 40% | 3,0 GB |
| NVDEC | 100 | 2.058 fps | 137 | 82% | 39% | 5,0 GB |

**Conclusões:**
- **Na CPU, 100 câmeras usam cerca de 57% deste processador** só com decode.
- **O NVDEC ficou em 39%: o limite foi a CPU do teste** (demux e laço Python), não o decodificador.
- **O NVDEC ocupa cerca de 50 MB de VRAM por câmera** (5 GB para 100). É o maior item de VRAM quando usado.

---

## 4. Teste ponta a ponta

N câmeras simuladas em tempo real, com decode, pose e EPI rodando juntos, decode na CPU e modelos FP16.

**Critério de aprovação:**
- pose e EPI atingem ao menos 95% da taxa-alvo;
- idade p95 do frame, da captura ao resultado, abaixo de 1 s;
- descarte de frames abaixo de 1%;
- decode acompanhando o tempo real.

### 4.1 Carga média: 2 pessoas por câmera

| Câmeras | Pose (% da taxa) | Pose p95 | EPI (% da taxa) | EPI p95 | GPU | CPU | VRAM (dispositivo) | Resultado |
|---|---|---|---|---|---|---|---|---|
| 50 | 100,0% | 81 ms | 99,4% | 140 ms | 25% | 32% | 8,0 GB | Aprovado |
| 75 | 100,0% | 112 ms | 100,6% | 312 ms | 38% | 53% | 8,0 GB | Aprovado |
| **90** | 99,9% | 133 ms | 100,5% | 801 ms | 44% | 65% | 8,0 GB | **Aprovado** |
| 100 | 99,9% | 164 ms | 98,8% | 1.404 ms | 49% | 77% | 8,0 GB | Reprovado (EPI p95) |

### 4.2 Pico: 5 pessoas por câmera

| Câmeras | Pose (% da taxa) | Pose p95 | EPI (% da taxa) | EPI p95 | GPU | CPU | VRAM (dispositivo) | Resultado |
|---|---|---|---|---|---|---|---|---|
| 25 | 99,9% | 68 ms | 99,9% | 164 ms | 20% | 18% | 8,0 GB | Aprovado |
| 40 | 99,9% | 82 ms | 99,9% | 238 ms | 34% | 29% | 8,1 GB | Aprovado |
| 50 | 99,9% | 94 ms | 99,8% | 302 ms | 39% | 37% | 8,1 GB | Aprovado |
| **60** | 99,8% | 117 ms | 100,3% | 554 ms | 48% | 48% | 8,1 GB | **Aprovado** |
| 70 | 99,9% | 117 ms | 91,7% | 1.593 ms | 49% | 54% | 8,0 GB | Reprovado (EPI satura em cerca de 600 inf/s) |
| 80 | 100,0% | 128 ms | 71,4% | 1.652 ms | 49% | 66% | 8,0 GB | Reprovado |

### 4.3 Decode no NVDEC: 100 câmeras, 2 pessoas

| Pose (% da taxa) | Pose p95 | EPI (% da taxa) | EPI p95 | GPU | CPU | VRAM (dispositivo) | Resultado |
|---|---|---|---|---|---|---|---|
| 95,3% | 1.488 ms | 94,7% | 1.618 ms | 64% | 95% | **15,9 GB** | Reprovado |

No teste, cada um dos 17 processos de captura abriu seu próprio contexto CUDA, somado aos cerca de 50 MB de cada decoder, e a VRAM da placa se esgotou. **Em produção, o decode na GPU precisa ficar concentrado em poucos processos (um por GPU), com o pré-processamento na própria GPU.**

### 4.4 Leitura dos resultados

- **Nas reprovações, a GPU fica parada em cerca de 49%.** O limite é o NMS em Python numa única thread do processo de inferência.
- **Com 100 câmeras e 2 pessoas, a latência de 1,4 s ainda cabe no RNF-002** (alerta em até 3 s) e na janela de confirmação de 20 s. O critério de 1 s do teste é mais rígido que a SRS.
- **VRAM:** cerca de 8,0 GB de pico no dispositivo, incluindo cerca de 1,5 GB do desktop Windows. A aplicação usa cerca de 6,5 GB, quase todo de contexto TensorRT (de 1,9 a 2,4 GB por engine com batch 32). O consumo não cresce com o número de câmeras quando o decode é na CPU.

---

## 5. Impacto no dimensionamento

| Tema | Premissa do capacity | Resultado medido | Decisão |
|---|---|---|---|
| VRAM | de 6 a 10 GB por GPU | cerca de 6,5 GB (decode na CPU); mais cerca de 50 MB por câmera com NVDEC | **12 GB é o mínimo; 16 a 20 GB é o confortável.** 24 GB não são necessários. |
| GPU | cerca de 26 TFLOPS efetivos para 100 câmeras | uma RTX 5080 atende 153 câmeras na média só com a rede, e 90 com o pipeline atual | 2 nós com 1 GPU cada (Opção A) se mantém |
| INT8 | ganho de cerca de 2× | sem ganho nesta GPU | **Usar FP16** |
| CPU | 32 núcleos para 100 câmeras | 77% de um i9-14900KF com 100 câmeras | **32 núcleos por nó** (núcleos de servidor têm clock menor) |
| Decode | NVDEC recomendado | CPU dá conta; NVDEC exige arquitetura de processo único por GPU | CPU como padrão; NVDEC só com pipeline na GPU |

**Conversão para a GPU de produção:** a L4 e a RTX 4000 Ada devem render de 40% a 50% de uma RTX 5080 nesta carga. É uma estimativa por banda de memória e desempenho FP16, ainda não medida. Para 50 câmeras por nó, isso dá:
- de 45% a 55% de uso na média e de 75% a 90% no pico, o que valida a Opção A;
- no modo degradado (100 câmeras num só nó), é preciso reduzir a taxa de inferência, como já previsto no capacity.md.

---

## 6. Próximos passos

1. **Eliminar o gargalo do NMS:**
   - embutir o NMS na engine (`export(nms=True)` ou o plugin EfficientNMS do TensorRT);
   - usar o modelo de EPI real, com 4 a 8 classes em vez de 80;
   - rodar 2 ou mais processos de inferência por GPU.

   Com isso, a GPU tende a se aproximar da capacidade pura medida (153 câmeras na média).
2. **Repetir a prova com gravações reais da planta** (`--videos`) e com o modelo de EPI treinado.
3. **Medir a GPU de produção** (L4 ou RTX 4000 Ada) para substituir a estimativa de 40% a 50% por um número real.
4. **Se o decode na GPU for adotado,** implementar decode e pré-processamento num único processo por GPU e repetir o teste da seção 4.3.

---

## 7. Limitações

- **O modelo de EPI é um substituto (`yolov8s`).** Ele tem o mesmo custo de rede, mas 80 classes, o que infla o NMS.
- **O vídeo é sintético e as pessoas são simuladas** com recortes fixos (`--persons`), o que mantém a carga do estágio de EPI constante.
- **RTSP não foi testado.** O decode lê arquivos; a rede é dimensionada à parte (cerca de 4 Mbps por câmera).
- **A RAM do sistema não foi medida de forma conclusiva:** a amostragem começa depois do aquecimento.
- **A engine INT8 do modelo de EPI não compila no TensorRT 10.16** nesta GPU (erro interno do compilador Myelin). O TensorRT 11 foi descartado porque a exportação via NVIDIA ModelOpt estourou a RAM.
- **Windows com GeForce difere de um servidor Linux com L4 ou RTX Ada.** Os números validam a ordem de grandeza, não o valor exato do hardware final.

### Arquivos de resultado

Em `benchmarks/results/`:

| Arquivo | Conteúdo |
|---|---|
| `infer_20261110_120814.json` | Inferência com NMS |
| `infer_20261110_120945.json` | Inferência só da rede (`--no-nms`) |
| `decode_20261110_121237.json` | Decode CPU vs NVDEC |
| `e2e_20261110_122011.json` | Ponta a ponta, 2 pessoas (50, 75, 90 e 100 câmeras), seção 4.1 |
| `e2e_20261110_122346.json` | Ponta a ponta, 5 pessoas (25, 40, 50 e 60 câmeras), seção 4.2 |
| `e2e_20261110_122635.json` | Ponta a ponta, 5 pessoas (25, 70 e 80 câmeras), seção 4.2 |
| `e2e_20261110_122750.json` | Ponta a ponta com NVDEC, 100 câmeras, seção 4.3 |

**Arquivos que não valem como resultado:**
- `e2e_20261110_121620.json` usa uma meta de taxa do EPI errada (2 Hz, quando o efetivo é 1,875 Hz) e deve ser desconsiderado.
- `e2e_20261110_122346.json` foi gerado antes da correção que zera os descartes do aquecimento. Por isso, a linha de 25 câmeras aparece reprovada nele. Ela foi repetida em `e2e_20261110_122635.json` e aprovada.
