# Arquitetura em cluster N+1 — P300 Vision Safety

Versão 1.0 · 12/11/2026

Proposta para trocar o par ativo-ativo do [capacity.md](capacity.md) v2.0 por um cluster de nós iguais, em que cada nó atende 20 câmeras. Para crescer, basta adicionar um nó. Os números vêm da prova de carga em RTX 5080 ([benchmark_capacity.md](benchmark_capacity.md)), e os componentes, do [hardware_industrial.md](hardware_industrial.md).

## Resumo

- **6 nós para 100 câmeras** (5 ativos + 1 de reserva). Cada 20 câmeras a mais exigem um nó a mais.
- **Tolerância a falhas:** 1 nó perdido sem degradar; até 3 nós perdidos com o modo degradado (pose a 3 fps, EPI a 1 Hz).
- **Custo para 100 câmeras:** cerca de **US$ 19 mil a 26 mil** com DDR4 ou US$ 25 mil a 36 mil com DDR5.
- **Expansão:** US$ 2,5 mil a 3,4 mil por nó de 20 câmeras, com DDR4.
- **Pré-requisitos de software:** NMS embutido na engine TensorRT, coordenador de câmeras, barramento de eventos e nós de inferência sem estado.

## 1. Por que mudar

No par ativo-ativo, cada nó aguenta sozinho as 100 câmeras para cobrir a falha do outro. Na operação normal, metade do hardware fica ociosa: a capacidade instalada é 200% da necessária. Com N+1, a reserva cai para 1/N:

| Câmeras | Par ativo-ativo | Cluster N+1 (nós de 20 câmeras) | Capacidade instalada |
|---|---|---|---|
| 100 | 2 nós grandes | 6 nós | 200% → 120% |
| 200 | 4 nós grandes | 11 nós | 200% → 110% |
| 300 | 6 nós grandes | 16 nós | 200% → 107% |

Além disso, a falha de um nó no par ativo-ativo leva o sobrevivente ao modo degradado. No N+1, os nós restantes absorvem as câmeras sem degradar.

## 2. Arquitetura

```
 Câmeras RTSP ──► MediaMTX (vídeo ao vivo para a UI)
      │
      ▼
 ┌─────────────── Plano de dados (nós iguais, sem estado) ───────────────┐
 │  Nó 1: decode + pose + EPI + regra de 20 s   (câmeras A..)             │
 │  Nó 2: idem                                   (câmeras ..)             │
 │  Nó N+1: idem              ◄── coordenador distribui as câmeras        │
 └──────┬──────────────────────────────┬──────────────────────────────────┘
        │ eventos (NATS / Redis Streams)│ clipes de evidência
        ▼                               ▼
 ┌─────────────── Plano de controle (3 réplicas) ────────────────────────┐
 │  API/UI sem estado + VIP │ PostgreSQL (Patroni) │ MinIO distribuído    │
 │  Coordenador de câmeras  │ etcd (quórum)        │ Observabilidade      │
 └────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Mudanças no software

1. **Nós de inferência sem estado.** Cada nó recebe uma lista de câmeras, faz decode, pose, EPI e a regra de 20 s, e publica eventos. O nó não grava em banco e não guarda nada que não possa perder.
2. **Coordenador de câmeras.** As atribuições ficam no etcd com *lease*: cada nó manda sinal de vida a cada 1 s, e o lease expira em cerca de 5 s.
   - **Nó cai:** as câmeras dele vão para os sobreviventes, de acordo com a folga de cada um.
   - **Nó entra:** o coordenador rebalanceia aos poucos, poucas câmeras por vez.
   - **Peso por câmera:** cada câmera tem um peso (pessoas típicas na cena, fps), o que permite misturar GPUs e gerações de hardware no mesmo cluster.

   É código próprio; o Kubernetes não distribui câmeras sozinho.
3. **Estado por câmera durante a migração.** O cronômetro de 20 s e os tracks se perdem quando a câmera muda de nó. Na pior hipótese, uma não conformidade em andamento é confirmada até cerca de 25 s mais tarde, uma vez a cada falha de nó.
   - **Opcional:** gravar no Redis o início de cada não conformidade aberta, para o nó novo retomar a contagem.
   - **SRS:** registrar esse comportamento junto ao RNF-002.
4. **Barramento de eventos** (NATS JetStream ou Redis Streams). Os nós publicam detecções e violações. Os serviços centrais cuidam de alerta, persistência, auditoria e deduplicação.
5. **Evidências direto para o MinIO distribuído.** O nó mantém o buffer de pré-alerta comprimido, com pacotes H.264 sem decodificar, e envia o clipe ao MinIO. O MinIO usa *erasure coding* entre os nós, então não há RAID por servidor.
6. **Vídeo ao vivo fora dos nós de inferência.** O MediaMTX ou o go2rtc redistribui o RTSP para a UI. As caixas e alertas vão por WebSocket, como metadados, e são desenhados no navegador. Isso tira o encode de MJPEG da CPU dos nós.
7. **Plano de controle com 3 réplicas.** PostgreSQL com Patroni, etcd e MinIO rodam nos 3 nós de controle, com CPU e RAM reservadas.
8. **Degradação elástica.** Se o cluster perder mais nós do que a reserva cobre, o coordenador reduz a taxa só o necessário e só nas câmeras de menor prioridade.
9. **Orquestração.** Recomenda-se k3s com o NVIDIA GPU Operator. Se a equipe do cliente não tiver experiência com Kubernetes, Docker Compose com systemd também funciona.

## 3. Dimensionamento do nó de 20 câmeras

Custo por câmera medido na RTX 5080: 5,2 ms de GPU por segundo na média e 8,4 ms no pico (5 pessoas). No modo degradado: 2,9 ms e 4,5 ms.

### 3.1 GPU

Com 20 câmeras, a carga equivale a 10% de uma RTX 5080 na média e 17% no pico. Meta: até 70% na média e até 90% no pico.

| GPU | Fator vs. RTX 5080 | 20 câmeras, média | 20 câmeras, pico | Preço estimado (US$) |
|---|---|---|---|---|
| **RTX 2000 Ada 16 GB** (70 W, perfil baixo) | 0,20 a 0,25 | 42% a 52% | 67% a 84% | 700 – 1.000 |
| RTX 4000 Ada 20 GB (130 W) | 0,40 a 0,50 | 21% a 26% | 34% a 42% | 1.250 – 1.500 |

**Escolhida: RTX 2000 Ada.**
- Na operação normal, cada nó fica com cerca de 17 câmeras: de 36% a 44% na média. Um nó só chega a 20 câmeras quando outro nó cai.
- Com 3 nós perdidos, os 3 restantes ficam com cerca de 33 câmeras cada no modo degradado: cerca de 66% no pico.
- O pipeline usa 6,5 GB fixos de VRAM, então 16 GB sobram.
- A RTX PRO 2000 Blackwell é candidata se o preço for parecido, mas o desempenho dela não foi medido.

**O NMS precisa rodar na GPU.** Com o NMS em Python, 20 câmeras no pico chegam a cerca de 138% numa RTX 2000 Ada.

### 3.2 CPU

20 câmeras usam de 3 a 4 núcleos de servidor no pipeline. Os serviços do cluster somam de 2 a 4 núcleos nos nós de controle. Por isso: 12 núcleos nos nós de controle e 8 nos nós de trabalho.

### 3.3 RAM

Estimativa, porque a prova não mediu a RAM com precisão.

| Componente | Nó de controle | Nó de trabalho |
|---|---|---|
| Inferência (fixa) | 8 GB | 8 GB |
| Captura, decode e pré-alerta de 20 câmeras | 4,5 GB | 4,5 GB |
| PostgreSQL | 8 GB | — |
| MinIO | 4 GB | 2 GB |
| etcd, NATS, k3s | 3 GB | 2 GB |
| Observabilidade | 8 GB | — |
| SO e cache | 8 GB | 6 GB |
| **Total** | **cerca de 43 GB → 64 GB** | **cerca de 23 GB → 32 GB** |

### 3.4 Disco

- **SO e banco:** NVMe com proteção contra queda de energia; espelhado nos nós de controle e simples nos de trabalho, que são reinstalados a partir de uma imagem.
- **Evidências:** em 180 dias, com 20 ocorrências por câmera por dia, são precisos cerca de 6 TB úteis (3,8 TB de evidências mais 2 TB para retreino).
  - **Desenho:** 1 HDD enterprise de 4 TB por nó, com MinIO em EC:2 entre os 6 discos.
  - **Resultado:** cerca de 16 TB úteis, e o cluster aguenta perder 2 discos ou 2 nós.

### 3.5 Rede

Entram cerca de 80 Mbps por nó (4 Mbps por câmera). **2× 1 GbE** bastam, com as câmeras numa VLAN dedicada.

## 4. Hardware por nó

Com N+1, a redundância é o próprio cluster. Só os 3 nós que guardam estado precisam de fonte redundante e discos espelhados.

### 4.1 Opção DDR4 (recomendada pelo custo)

Em 2026, o DDR4 ECC custa cerca de US$ 8,40/GB, contra cerca de US$ 31,75/GB do DDR5 ECC.

| Item | Nó de controle (3 unidades) | Nó de trabalho |
|---|---|---|
| Gabinete e fonte | Advantech ACP-4340 com fonte redundante 1+1 de 500 W | 4U industrial com fonte simples |
| Placa-mãe | ASRock Rack X570D4U (AM4, DDR4 ECC UDIMM, IPMI, 2× 1 GbE Intel) | Igual |
| CPU | Ryzen 9 5900X (12 núcleos) | Ryzen 7 5700X (8 núcleos) |
| RAM | 64 GB DDR4-3200 ECC (2× 32 GB) | 32 GB DDR4-3200 ECC (2× 16 GB) |
| GPU | RTX 2000 Ada 16 GB | Igual |
| SO e banco | 2× NVMe de 960 GB com proteção contra queda de energia, espelhados | 1× NVMe de 960 GB com proteção contra queda de energia |
| Evidências | 1× HDD enterprise de 4 TB para o MinIO | Igual |
| Consumo | cerca de 200 a 250 W | cerca de 200 W |
| **Custo estimado (US$)** | **3.300 – 4.600** | **2.500 – 3.400** |

**Cuidados com a opção DDR4:**
1. **AM4 é uma plataforma em fim de vida.** Inclua no kit de sobressalentes 1 placa-mãe e 1 CPU (cerca de US$ 500). Nós futuros podem ser DDR5, porque o coordenador aceita hardware misto.
2. **ECC no Ryzen comum** é suportado pela placa, mas não é validado oficialmente pela AMD. Confirme no burn-in (`edac-util` ou log do BMC), ou use Ryzen PRO 5000.
3. **BIOS atualizada** é necessária para a Ryzen 5000.
4. **O preço do DDR4 sobe mais rápido** que o do DDR5, porque a produção está sendo encerrada. Compre toda a memória de uma vez.

### 4.2 Opção DDR5

| Item | Nó de controle | Nó de trabalho |
|---|---|---|
| Placa-mãe | ASRock Rack B650D4U (AM5, ECC, IPMI, 2× 1 GbE) | Igual |
| CPU | EPYC 4465P (12 núcleos) | EPYC 4345P (8 núcleos) |
| RAM | 64 GB DDR5 ECC | 32 GB DDR5 ECC |
| Demais itens | Iguais à opção DDR4 | |
| **Custo estimado (US$)** | **4.700 – 6.900** | **3.200 – 4.500** |

## 5. Custo para 100 câmeras

| Item | DDR4 (US$) | DDR5 (US$) |
|---|---|---|
| 3 nós de controle | 9.900 – 13.800 | 14.100 – 20.600 |
| 3 nós de trabalho | 7.500 – 10.200 | 9.600 – 13.500 |
| Kit de sobressalentes (GPU, módulo de fonte, NVMe, HDD) | 1.200 – 1.800 | 1.200 – 1.800 |
| **Total** | **19.000 – 26.000** | **25.000 – 36.000** |
| **Total em reais** (câmbio R$ 5,52 e impostos de importação) | **cerca de R$ 150 mil – 240 mil** | **cerca de R$ 200 mil – 330 mil** |

Comparação com os outros desenhos:

| Desenho | Custo para 100 câmeras (US$) | Custo para crescer | Falhas toleradas |
|---|---|---|---|
| 2 nós de 100 câmeras, ativo-ativo ([hardware_industrial.md](hardware_industrial.md)) | 19.000 – 28.000 | Outro par de nós | 1, já no modo degradado |
| 3 nós de 50 câmeras | 23.000 – 33.000 | 7.000 – 10.000 por 50 câmeras | 1 sem degradar |
| **6 nós de 20 câmeras, DDR4** | **19.000 – 26.000** | **2.500 – 3.400 por 20 câmeras** | **1 sem degradar, até 3 degradando** |

Os valores são estimativas com preços de revendedores dos EUA e da Europa em novembro de 2026, não cotação em reais.

## 6. Validações pendentes

1. **Failover:** derrubar um nó com o cluster carregado e medir o tempo de redistribuição das câmeras (meta: menos de 10 s) e o SLO nos nós restantes.
2. **RTX 2000 Ada:** rodar o `benchmarks/gpu_load_test.py e2e --cams 20 --persons 5` na placa para confirmar o fator de 0,20 a 0,25.
3. **RAM real** dos processos de captura e inferência com 20 câmeras.
4. **Ryzen 5700X:** confirmar o uso de CPU com 20 câmeras e os serviços de controle.

## Fontes

- [computingforgeeks – RAM prices 2027](https://computingforgeeks.com/ram-prices-2027/)
- [datacenterdisk – Server RAM Price Index](https://datacenterdisk.com/server-ram/price-index)
- [Guru3D – DDR4 prices rise as shortages intensify](https://www.guru3d.com/story/ddr4-memory-prices-now-also-rise-as-dram-supply-shortages-intensify-through-2028/)
- [Sourceability – The DDR4 paradox](https://sourceability.com/post/the-ddr4-paradox-legacy-memory-prices-are-rising-faster-than-ddr5)
- [Tom's Hardware – DDR4 production restarting](https://www.tomshardware.com/pc-components/ram/production-of-ddr4-memory-and-motherboards-is-restarting-amid-unprecedented-memory-shortages-pc-industry-preparing-for-a-world-without-ddr5)
- [SHI – ASRock Rack X570D4U](https://www.shi.com/product/40716725/ASRock-Rack-X570D4U-Motherboard)
- [Newegg Business – X570D4U](https://www.neweggbusiness.com/asrock-rack-x570d4u-supports-3rd-gen-amd-ryzen-processors-and-2nd-gen-amd-ryzen-processors-with-rade/p/9B-13-140-057)
- [Advantech – ACP-4340 4U](https://buy.advantech.com/Rackmount-Systems/Industrial-Computers-Rackmount-Chassis-By-Height-4U/model-ACP-4340MB-00XE.htm)
- [Newegg – ASRock Rack B650D4U-2L2T/BCM](https://www.newegg.com/asrock-rack-b650d4u-2l2t-bcm-amd-ryzen-7000-series-processors/p/N82E16813140099)
