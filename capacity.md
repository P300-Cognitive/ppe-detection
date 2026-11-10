# P300 Vision Safety — Dimensionamento de Servidor (Capacity)

**Referência:** [P300_Vision_Safety_SRS_v1.0.md](P300_Vision_Safety_SRS_v1.0.md)
**Escopo:** até 100 câmeras IP simultâneas
**Data:** 10/11/2026
**Status:** estimativa preliminar, a validar com prova de carga

> **Resumo:** para 100 câmeras, recomenda-se **2 servidores em alta disponibilidade, cada um com 1× NVIDIA L4, 32 núcleos e 128 GB de RAM**, mais armazenamento de evidências de 8 a 16 TB úteis. Se o cliente aceitar o risco de um servidor único, ele precisa de 2× L4.
>
> Os números de GPU são estimativas por FLOPs e por referências públicas de TensorRT, não medições. Devem ser confirmados com o benchmark descrito na seção 5.

---

## 1. Impacto dos requisitos da SRS no capacity

| Requisito da SRS | Efeito no capacity |
|---|---|
| **Confirmação de 20 s por timestamp** (RN-001, RN-002) | Não é preciso inferir a 15 fps. Com 5 fps para rastrear pessoas e 1 a 2 avaliações de EPI por segundo, há de 20 a 40 amostras por violação. **A GPU cai cerca de 3×.** |
| **EPIs de vidraria: óculos transparentes, luvas da cor da pele, calçado** (seção 4, exemplo da Linha de Corte; seção 13.1) | São objetos pequenos. É preciso **resolução 1080p na origem** e avaliação em **dois estágios** (detecta a pessoa e analisa o recorte dela em alta resolução). Isso aumenta o custo por pessoa. |
| **Estado "indeterminado"** (RN-005, seção 5.1) | É preciso saber se mãos, pés e rosto estão visíveis. Recomenda-se trocar o detector de pessoas por um modelo de **pose** (YOLOv8s-pose), que também melhora a associação de luva com mão e de óculos com olhos. |
| **ROI por câmera** (RF-015) | Só pessoas dentro da zona vão para o 2º estágio, o que reduz carga. |
| **Visualização ao vivo independente do processamento** (seção 7.1, CA-007) e **mosaico** (RF-066) | Repassar o stream da câmera sem recodificar (MediaMTX ou go2rtc, via WebRTC ou HLS) e desenhar as caixas no navegador. A CPU de visualização fica perto de zero. |
| **99,5% de disponibilidade** (RNF-001) | São 3,6 h de parada por mês, contando manutenção. Isso pede **2 nós**, ou no mínimo GPU e fonte redundantes. |
| **Não perder ocorrência confirmada** (RNF-006) | PostgreSQL replicado e fila persistente. |
| **Evidência com hash, retenção e object storage** (RNF-012, RF-081, seção 8.2) | MinIO para imagens e vídeos. O clipe é cópia do stream original, sem recodificar, o que custa pouca CPU e preserva a integridade. |

---

## 2. Premissas

A seção 14.1 da SRS deixa estas decisões pendentes com o cliente; precisam ser validadas:

- 100 câmeras com stream principal de 1080p, H.264 ou H.265, de 10 a 15 fps, com 2 a 4 Mbps.
- Em média 2 pessoas por câmera e pico de 5.
- De 5 a 50 ocorrências por câmera por dia.
- Evidência por ocorrência: 2 imagens (recorte e contexto, cerca de 0,6 MB) mais um clipe de 20 s (cerca de 10 MB), ou seja, **cerca de 10,6 MB**.
- Retenção de 90 a 180 dias, a definir pela política de LGPD.

---

## 3. Carga calculada

### 3.1 GPU

Com TensorRT, considerando só 20% do pico de FP16 como aproveitamento real:

| Estágio | Taxa | Média | Pico (5 pessoas) |
|---|---|---|---|
| Pose + pessoas (YOLOv8s-pose, 640) | 100 câmeras × 5 fps | 15 TFLOPS | 15 TFLOPS |
| EPI no recorte da pessoa (YOLOv8s, 640) | pessoas × 2 por segundo | 11 TFLOPS | 29 TFLOPS |
| **Total** | | **cerca de 26 TFLOPS** | **cerca de 44 TFLOPS** |

- Uma L4 entrega cerca de 25 TFLOPS efetivos em FP16, e cerca de 50 em INT8.
- **Em INT8, 1 L4 aguenta a média e 2 L4 aguentam o pico com folga.**
- VRAM: de 6 a 10 GB por GPU, somando engines, batch e superfícies de decode. Os 24 GB da L4 sobram.

### 3.2 Decode de vídeo

- 100 streams 1080p custam de 7 a 10 núcleos em H.264. Em H.265, que é comum em câmera IP, o custo quase dobra.
- O **NVDEC da L4** decodifica esses streams na própria GPU. É a opção recomendada.

### 3.3 CPU

Decode por software (reserva), pré e pós-processamento, 10 workers de câmera, rastreamento, regras, API, PostgreSQL, MinIO e observabilidade somam de 20 a 28 núcleos. **Recomendação: 32 núcleos.**

### 3.4 Memória RAM

| Componente | Memória |
|---|---|
| Inferência TensorRT | 8 GB |
| 10 workers de captura | 15 GB |
| Buffers de decode | 6 GB |
| Buffer de pré-alerta comprimido | 1 GB |
| PostgreSQL | 16 GB |
| MinIO | 4 GB |
| Prometheus, Grafana e Loki | 8 GB |
| SO e cache | 16 GB |
| **Total** | **cerca de 75 GB; recomendação: 128 GB** |

### 3.5 Disco de evidências

100 câmeras × 10,6 MB por ocorrência:

| Ocorrências por câmera por dia | Por dia | 90 dias | 180 dias |
|---|---|---|---|
| 5 | 5,3 GB | 0,5 TB | 1 TB |
| 20 | 21 GB | 1,9 TB | 3,8 TB |
| 50 | 53 GB | 4,8 TB | 9,5 TB |

Somar ainda:

- Coleta de vídeos para validação e retreino do modelo (RF-031, seção 13.1): cerca de 1 a 2 TB.
- Banco, auditoria e logs: menos de 200 GB por ano.

A taxa de gravação é baixa (menos de 1 MB/s), então **HDD em RAID6 serve para as evidências**. Banco e SO precisam de NVMe.

### 3.6 Rede

- Entrada: de 200 a 400 Mbps.
- Visualização: cerca de 4 Mbps por câmera assistida.
- Recomendação: **2× 10 GbE**, com as câmeras numa VLAN separada da rede de usuários.

---

## 4. Configuração recomendada

### Opção A — 2 nós ativo-ativo (recomendada, atende 99,5%)

Cada nó atende 50 câmeras. Se um nó cair, o outro assume as 100, baixando a inferência para cerca de 2 a 3 fps. A janela de 20 s continua sendo cumprida, o que torna esse modo degradado viável.

| Item | Por nó |
|---|---|
| CPU | 1× 32 núcleos (EPYC 9355P / 9354P ou Xeon Gold 6530) |
| RAM | 128 GB DDR5 ECC |
| GPU | 1× NVIDIA L4 24 GB (inferência + NVDEC) |
| SO e aplicação | 2× 960 GB NVMe em RAID1 |
| PostgreSQL | 2× 1,92 TB NVMe em RAID1, com replicação entre os nós |
| Evidências | 4× 8 TB HDD em RAID6 (cerca de 16 TB úteis), com MinIO replicado entre os nós |
| Rede | 2× 10 GbE |
| Outros | Fonte redundante, BMC/IPMI, suporte NBD |

Incluir também backup externo das evidências e do banco, e um nobreak.

### Opção B — 1 nó (mais barata, não garante 99,5%)

A mesma configuração, com **2× L4** e o dobro de disco de evidências. Ela sobrevive à falha de uma GPU, mas não à da placa-mãe, da fonte ou de uma manutenção longa.

### Fases menores

| Câmeras | GPU | CPU | RAM |
|---|---|---|---|
| até 25 | 1× L4 (ou RTX 4000 Ada) | 16 núcleos | 64 GB |
| até 50 | 1× L4 | 24 núcleos | 96 GB |
| até 100 | conforme as opções A ou B | | |

A arquitetura da SRS (workers separados e inferência centralizada) permite crescer adicionando nós, como prevê a Fase 3.

---

## 5. Fatores que podem alterar o dimensionamento

1. **Pessoas por cena e quantas câmeras exigem óculos ou luvas.** É a variável que mais pesa na GPU. Se várias câmeras tiverem mais de 5 pessoas simultâneas, a carga sobe linearmente.
2. **Câmeras 4 MP ou H.265** aumentam a carga de decode e de rede, sem efeito relevante na GPU de inferência.
3. **Modelo final.** O modelo próprio treinado ainda não existe. Este dimensionamento assume duas redes da classe YOLOv8s com TensorRT INT8.
4. **Prova de carga.** Antes da compra, executar um benchmark numa RTX 5080 com PyTorch CUDA e TensorRT, usando gravações reais da planta. A 5080 tem desempenho parecido com o de 2 L4, então serve para validar a premissa de cerca de 26 TFLOPS e o NVDEC com 50 streams.
