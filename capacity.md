# P300 Vision Safety — Dimensionamento de Servidor (Capacity)

**Versão:** 2.0, revisada com a prova de carga
**Referências:** [P300_Vision_Safety_SRS_v1.0.md](P300_Vision_Safety_SRS_v1.0.md) · [benchmark_capacity.md](benchmark_capacity.md)
**Escopo:** até 100 câmeras IP simultâneas
**Data:** 10/11/2026

> **Resumo:** para 100 câmeras com 99,5% de disponibilidade, recomenda-se **2 servidores ativo-ativo**, cada um com:
> - **1× NVIDIA RTX PRO 4000 Blackwell 24 GB** (alternativa: RTX 4000 Ada 20 GB ou L4 24 GB, com menos folga no pico);
> - **32 núcleos** e **128 GB de RAM**;
> - armazenamento de evidências de 8 a 16 TB úteis.
>
> Cada nó atende 50 câmeras e assume as 100 em modo degradado se o outro cair.
>
> **Pré-requisito de software:** o NMS (filtragem das detecções) precisa rodar dentro da engine TensorRT, e o modelo de EPI precisa ter poucas classes. Sem isso, o pipeline usa o dobro de GPU e cada nó precisaria de 2 GPUs (seção 3.3).

---

## 1. O que mudou em relação à versão 1.0

| Tema | v1.0 (estimativa) | v2.0 (medido na RTX 5080) |
|---|---|---|
| Base de cálculo da GPU | TFLOPS teóricos, 20% de aproveitamento | Tempo de GPU medido por câmera: 4,5 ms (2 pessoas) e 7,3 ms (5 pessoas) |
| INT8 | ganho de cerca de 2× | **sem ganho**; usar FP16 |
| Gargalo | GPU | **NMS em Python** (a GPU ficou em 49% nas falhas) |
| Decode | NVDEC recomendado | **CPU como padrão.** NVDEC custa cerca de 50 MB de VRAM por câmera e só funciona bem com o pipeline num único processo por GPU. |
| VRAM | de 6 a 10 GB | **6,5 GB medidos**; não é mais critério de escolha |
| GPU recomendada | 1× L4 por nó | **1× RTX PRO 4000 Blackwell** por nó (mesma arquitetura da GPU testada, mais folga no pico) |
| CPU | 32 núcleos | confirmado: 100 câmeras usaram 77% de um i9-14900KF |

---

## 2. Requisitos da SRS e premissas

### 2.1 Impacto dos requisitos da SRS

| Requisito da SRS | Efeito no capacity |
|---|---|
| **Confirmação de 20 s por timestamp** (RN-001, RN-002) | Pose a 5 fps e EPI a cerca de 2 avaliações por segundo por pessoa bastam (de 20 a 40 amostras por violação). No modo degradado, 3 fps e 1 Hz ainda dão 20 amostras. |
| **EPIs de vidraria: óculos, luvas, calçado** (seção 4; seção 13.1) | Stream 1080p na origem e avaliação em 2 estágios: pose na cena e EPI no recorte de cada pessoa. |
| **Estado "indeterminado"** (RN-005) | Modelo de pose (`yolov8s-pose`) para saber se mãos, pés e rosto estão visíveis. |
| **ROI por câmera** (RF-015) | Só pessoas dentro da zona vão ao estágio de EPI, o que reduz carga. |
| **Visualização ao vivo independente** (CA-007, RF-066) | Repasse do stream sem recodificar (MediaMTX ou go2rtc), com as caixas desenhadas no navegador. |
| **99,5% de disponibilidade** (RNF-001) | 2 nós ativo-ativo. |
| **Não perder ocorrência** (RNF-006) | PostgreSQL replicado e fila persistente. |
| **Evidência com hash e retenção** (RNF-012, RF-081) | MinIO replicado, com o clipe copiado do stream original. |

### 2.2 Premissas operacionais

A seção 14.1 da SRS deixa estas decisões pendentes com o cliente:

- 100 câmeras, 1080p, H.264 ou H.265, 15 fps, de 2 a 4 Mbps.
- Em média 2 pessoas por câmera e pico de 5.
- De 5 a 50 ocorrências por câmera por dia.
- Cerca de 10,6 MB de evidência por ocorrência (2 imagens e um clipe de 20 s).
- Retenção de 90 a 180 dias.

### 2.3 Premissas de software (derivadas da prova de carga)

1. **NMS embutido na engine TensorRT** (`export(nms=True)` ou o plugin EfficientNMS).
2. **Modelo de EPI com 4 a 8 classes**, da classe "s" (custo de rede igual ao `yolov8s`).
3. **Um processo de inferência por GPU, com batching entre câmeras** (batch de 16 a 32), em **FP16**.
4. **Decode na CPU**, em processos de captura de 6 a 12 câmeras cada, convertendo para imagem só os frames amostrados.

---

## 3. Base de cálculo

### 3.1 Custo medido por câmera (RTX 5080)

Dados detalhados no [benchmark_capacity.md](benchmark_capacity.md).

| Componente | 2 pessoas | 5 pessoas |
|---|---|---|
| Rede pura (pose 5 fps + EPI 2 Hz por pessoa) | 4,5 ms de GPU/s | 7,3 ms de GPU/s |
| **Com NMS na GPU, +15% de margem** (base deste documento) | **5,2 ms/s** | **8,4 ms/s** |
| Com o NMS em Python atual (medido) | 8,4 ms/s | 15,6 ms/s |
| Modo degradado (pose 3 fps, EPI 1 Hz), com margem | 2,9 ms/s | 4,5 ms/s |

### 3.2 Conversão para GPUs de servidor

O fator abaixo é o desempenho relativo a uma RTX 5080 nesta carga. **São estimativas por banda de memória e FP16 tensor, ainda não medidas.** A seção 7 prevê a validação.

| GPU | VRAM | Fator vs. RTX 5080 | Observação |
|---|---|---|---|
| RTX 2000 Ada | 16 GB | 0,20 a 0,25 | 70 W, para fases pequenas |
| L4 | 24 GB | 0,40 a 0,50 | Passiva, 72 W, exige chassi com fluxo de ar |
| RTX 4000 Ada | 20 GB | 0,40 a 0,50 | Blower, 130 W, slot simples |
| **RTX PRO 4000 Blackwell** | 24 GB | **0,60 a 0,70** | Blower, slot simples, mesma arquitetura da GPU testada |

Uso da GPU = câmeras × custo por câmera ÷ fator ÷ 1.000 ms.

### 3.3 Uso de GPU por nó

Valores calculados com o fator no meio da faixa (0,45 e 0,65). Meta: até 70% na média e até 90% no pico.

| Cenário | RTX 4000 Ada / L4 | RTX PRO 4000 Blackwell |
|---|---|---|
| 50 câmeras, média (2 pessoas) | 58% | **40%** |
| 50 câmeras, pico (5 pessoas) | **93%** (no limite) | **65%** |
| 100 câmeras degradado, média | 64% | **45%** |
| 100 câmeras degradado, pico | **100%** (não cabe) | **69%** |
| 50 câmeras com NMS em Python, média | 93% | 65% |
| 50 câmeras com NMS em Python, pico | 173% (não cabe) | 120% (não cabe) |

**Conclusões:**
- A **RTX PRO 4000 Blackwell** cumpre todos os cenários com folga, inclusive o failover de 100 câmeras.
- A **RTX 4000 Ada ou a L4** cumprem a operação normal, mas ficam no limite no pico e **não aguentam o failover no pico**.
- **Sem o NMS na GPU, nenhuma GPU única por nó atende o pico.** É requisito de software antes da implantação.

### 3.4 CPU

Medido no i9-14900KF (32 threads):

| Cenário | Uso medido |
|---|---|
| Decode de 100 câmeras | 57% |
| Pipeline completo, 50 câmeras | 32% |
| Pipeline completo, 100 câmeras | 77% |

Estima-se que o i9-14900KF equivale a 24 a 28 núcleos de servidor (EPYC Zen 4) nesta carga. Isso dá:

- 50 câmeras: de 8 a 10 núcleos;
- 100 câmeras (failover): de 19 a 22 núcleos;
- mais API, PostgreSQL, MinIO e observabilidade: de 4 a 6 núcleos.

**32 núcleos por nó** dá de 40% a 50% de uso na operação normal e cerca de 80% no failover.

Uma alavanca opcional: configurar as câmeras a **10 fps** em vez de 15 reduz o decode em 33%, sem afetar a inferência (pose a 5 fps e EPI a cerca de 2 Hz continuam possíveis).

### 3.5 VRAM

| Item | Medido / estimado |
|---|---|
| Engines TensorRT (pose + EPI, batch 32, com contextos) | cerca de 4,5 GB |
| Contexto CUDA, buffers e PyTorch | cerca de 2 GB |
| **Total por GPU, com decode na CPU** | **cerca de 6,5 GB** (independe do número de câmeras) |
| Com NVDEC (opcional) | mais cerca de 50 MB por câmera: +2,5 GB (50) ou +5 GB (100) |

As GPUs recomendadas têm de 20 a 24 GB. **A VRAM sobra e não é critério de escolha.** Batch 16 em vez de 32 reduz cerca de 1 GB, com perda de throughput menor que 3%.

### 3.6 RAM

A prova não mediu a RAM de forma conclusiva. Mantida a estimativa da v1.0:

| Componente | Memória |
|---|---|
| Inferência | 8 GB |
| Workers de captura | 15 GB |
| Buffers de decode | 6 GB |
| Buffer de pré-alerta comprimido | 1 GB |
| PostgreSQL | 16 GB |
| MinIO | 4 GB |
| Observabilidade | 8 GB |
| SO e cache | 16 GB |
| **Total** | **cerca de 75 GB no failover; 128 GB por nó** |

### 3.7 Disco de evidências

100 câmeras × 10,6 MB por ocorrência:

| Ocorrências por câmera por dia | Por dia | 90 dias | 180 dias |
|---|---|---|---|
| 5 | 5,3 GB | 0,5 TB | 1 TB |
| 20 | 21 GB | 1,9 TB | 3,8 TB |
| 50 | 53 GB | 4,8 TB | 9,5 TB |

Somar de 1 a 2 TB para vídeos de validação e retreino (RF-031) e menos de 200 GB por ano de banco, auditoria e logs. A gravação é inferior a 1 MB/s, então **HDD em RAID6** atende as evidências.

### 3.8 Rede

- Entrada: de 200 a 400 Mbps para 100 câmeras.
- Visualização: cerca de 4 Mbps por câmera assistida.
- **2× 10 GbE por nó**, com as câmeras numa VLAN dedicada.

---

## 4. Configuração recomendada

### Opção A — 2 nós ativo-ativo (recomendada, atende 99,5%)

Operação normal: 50 câmeras por nó. Failover: 100 câmeras num nó, com pose a 3 fps e EPI a 1 Hz.

| Item | Por nó |
|---|---|
| CPU | 1× 32 núcleos (AMD EPYC 9355P / 9354P ou Intel Xeon 6530) |
| RAM | 128 GB DDR5 ECC (4× 32 GB) |
| GPU | **1× NVIDIA RTX PRO 4000 Blackwell 24 GB** |
| SO e aplicação | 2× 960 GB NVMe em RAID1 |
| PostgreSQL | 2× 1,92 TB NVMe em RAID1, com replicação entre os nós |
| Evidências | 4× 8 TB HDD em RAID6 (cerca de 16 TB úteis), com MinIO replicado entre os nós |
| Rede | 2× 10 GbE |
| Outros | Fonte redundante, BMC/IPMI, suporte NBD |

Incluir backup externo de evidências e banco, e nobreak.

**Alternativa de menor custo:** RTX 4000 Ada 20 GB ou L4 24 GB por nó. Atende a operação normal (58% na média e 93% no pico). No failover, porém, só sustenta 100 câmeras com até 3 ou 4 pessoas por câmera (de 76% a 88% de GPU); com 5 pessoas chega a 100%, e seria preciso reduzir ainda mais a taxa. **Só é recomendável se o cliente aceitar essa restrição no modo degradado.**

### Opção B — 1 nó (mais barata, não garante 99,5%)

| Item | Configuração |
|---|---|
| CPU | 1× 32 núcleos |
| RAM | 128 GB |
| GPU | **2× RTX PRO 4000 Blackwell 24 GB** (50 câmeras por GPU) |
| Disco | Igual à Opção A, com o dobro de evidências (sem a réplica do outro nó) |
| Rede | 2× 10 GbE |

Sobrevive à falha de uma GPU (a outra assume 100 câmeras em modo degradado), mas não à da placa-mãe, da fonte ou de uma manutenção.

### Fases menores

| Câmeras | GPU | Uso de GPU (média / pico) | CPU | RAM |
|---|---|---|---|---|
| até 25 | 1× RTX 2000 Ada 16 GB | 58% / 93% | 16 núcleos | 64 GB |
| até 25 (com folga) | 1× RTX 4000 Ada 20 GB | 29% / 47% | 16 núcleos | 64 GB |
| até 50 | 1× RTX PRO 4000 Blackwell 24 GB | 40% / 65% | 24 núcleos | 96 GB |
| até 100 | Opção A ou B | | | |

---

## 5. Modo degradado (failover)

| Parâmetro | Normal | Degradado |
|---|---|---|
| Pose por câmera | 5 fps | 3 fps |
| EPI por pessoa | cerca de 2 Hz | 1 Hz |
| Amostras na janela de 20 s | de 20 a 40 | 20 |
| Latência esperada do alerta | menos de 1 s | de 1 a 2 s (dentro do RNF-002, 3 s) |

A troca de modo deve ser automática ao detectar a queda do outro nó, e precisa gerar um evento operacional (RN-009).

---

## 6. Fatores que podem alterar o dimensionamento

1. **Pessoas por cena.** É a variável que mais pesa na GPU. Câmeras com mais de 5 pessoas simultâneas aumentam a carga linearmente.
2. **NMS fora da GPU.** Mantendo o NMS em Python, a carga de GPU dobra (seção 3.3).
3. **Modelo de EPI maior que a classe "s"** (por exemplo, "m"): o custo do estágio de EPI aumenta de 2 a 3×.
4. **Câmeras 4 MP ou H.265:** mais decode e rede, sem efeito relevante na GPU.
5. **Fator de conversão das GPUs:** estimado, não medido. Se a RTX PRO 4000 Blackwell render abaixo de 0,55×, o failover no pico fica no limite.

---

## 7. Validações antes da compra

1. **Implementar o NMS na engine** e repetir o `e2e` na RTX 5080. Meta: aproximar-se da capacidade pura (cerca de 150 câmeras na média).
2. **Repetir a prova com gravações reais** da planta (`--videos`) e com o modelo de EPI treinado.
3. **Medir a GPU escolhida** (RTX PRO 4000 Blackwell ou RTX 4000 Ada), por empréstimo, demonstração ou instância em nuvem, para substituir o fator estimado da seção 3.2.
4. **Medir a RAM real** dos processos de captura e inferência durante o `e2e`.
