# Servidor industrial de montagem própria — P300 Vision Safety

Versão 1.0 · 10/11/2026

Especificação de hardware para quem preferir montar os servidores com componentes avulsos, em vez de comprar um servidor de fabricante (HPE, Dell). Baseada no [capacity.md](capacity.md) v2.0 e na prova de carga em RTX 5080 ([benchmark_capacity.md](benchmark_capacity.md)).

## Resumo

- **2 servidores rack 4U industriais** em ativo-ativo, com 50 câmeras cada no normal e 100 num único nó em failover (modo degradado). É a mesma arquitetura do capacity, que atende à disponibilidade de 99,5% (RNF-001).
- **Kit de peças sobressalentes no local**, no lugar da garantia on-site de 4 horas de um fabricante.
- **Custo estimado: US$ 19 mil a 28 mil**, cerca de **R$ 150 mil a 260 mil** no Brasil. É menos da metade das opções HPE e Dell.
- **Contrapartida:** a equipe vira o integrador. O suporte passa a ser próprio, com garantia separada por componente.

Os valores são estimativas com preços de revendedores dos EUA e da Europa em novembro de 2026, não cotação em reais.

## Componentes por nó

| Componente | Recomendação | Por que | Estimativa (US$) |
|---|---|---|---|
| **Gabinete** | Advantech ACP-4340, 4U industrial, com filtro de ar e baias 3,5" com amortecimento | Linha industrial, com ventilação filtrada e pressão positiva | 300 – 750 |
| **Fonte** | Redundante 1+1 de 800 a 900 W (ex.: FSP Twins Pro), com troca a quente | Elimina a fonte como ponto único de falha | 400 – 600 |
| **Placa-mãe** | ASRock Rack B650D4U-2L2T/BCM: AM5, ECC, BMC/IPMI para gerência remota, 2× 10 GbE integradas | Recursos de servidor a preço de desktop; já traz o 10 GbE | cerca de 415 |
| **CPU** | AMD EPYC 4565P (16 núcleos, 32 threads, Zen 5), versão "servidor" do Ryzen 9 9950X, com ECC validado | Multithread equivalente ou superior ao i9-14900KF da prova, que aguentou 100 câmeras com 77% de CPU | cerca de 600 |
| **Memória** | 96 GB DDR5 ECC (2× 48 GB) | Atende os cerca de 75 GB do failover. ECC é obrigatório para operação 24×7. | 3.000 – 4.500 |
| **GPU** | NVIDIA RTX PRO 4000 Blackwell 24 GB (140 W, ventoinha blower, slot simples, memória com ECC) | Numa montagem própria não há homologação a respeitar. A blower expulsa o ar quente do gabinete, e a licença do driver permite uso em servidor. | 1.600 – 3.000 |
| **SO e banco** | 2× NVMe enterprise de 1,92 TB com proteção contra queda de energia (ex.: Micron 7450 PRO M.2), em espelho ZFS | Queda de energia em fábrica é comum, e a proteção evita corromper o banco | 600 – 1.000 |
| **Evidências** | 2× HDD enterprise de 8 TB (WD Ultrastar ou Seagate Exos), em espelho, replicado entre os nós | Custo por TB baixo; a taxa de gravação é inferior a 1 MB/s | cerca de 800 |
| Diversos | Trilhos, cabos, ventoinhas reserva | | cerca de 150 |
| **Total por nó** | | | **cerca de 8.000 – 11.800** |

### Desempenho esperado

Com a RTX PRO 4000, usando o fator estimado de 0,65× a RTX 5080:

| Situação | Uso de GPU (média) | Uso de GPU (pico) |
|---|---|---|
| 50 câmeras por nó | 40% | 65% |
| Failover, 100 câmeras em modo degradado | — | 69% |

**CPU no failover:** com 100 câmeras, o EPYC 4565P deve ficar entre 80% e 85%, somando os serviços. Para mais folga, configure as câmeras a 10 fps, o que corta 33% do decode.

## Kit de sobressalentes no local

| Item | Estimativa (US$) |
|---|---|
| 1× GPU RTX PRO 4000 | 1.600 – 3.000 |
| 1× módulo de fonte | 150 – 250 |
| 1× NVMe e 1× HDD | 700 – 900 |
| 1× par de pentes de memória (opcional) | 1.500 – 2.250 |
| **Total** | **cerca de 3.000 – 4.500** |

## Custo total

| Item | US$ |
|---|---|
| 2 nós | 16.000 – 23.600 |
| Kit de sobressalentes | 3.000 – 4.500 |
| **Total** | **19.000 – 28.000** |
| **Total em reais** (câmbio R$ 5,52 e impostos de importação, de 40% a 70% a mais) | **cerca de R$ 150 mil – 260 mil** |

Componentes avulsos, sobretudo a GPU, pagam muito imposto na importação, por isso a faixa em reais é larga. Vale cotar com distribuidores nacionais como PNY Brasil, Advantech Brasil e Kingston.

## Alternativa: computadores robustos junto às linhas

Para distribuir o processamento perto das câmeras, em vez de numa sala central, a opção são computadores industriais de borda.

- O **Neousys Nuvo-9160GC** opera de -25 °C a 60 °C, usa Intel Core de 12ª a 14ª geração e aceita GPU RTX de 130 a 150 W. Com CPU de 65 W, o limite de temperatura cai para 50 °C.
- **Com a RTX PRO 4000 de 140 W**, se o modelo aceitar 150 W: cerca de 50 câmeras por unidade.
- **Com a RTX PRO 4000 SFF** (70 W, 432 GB/s, cerca de US$ 1.500): só 25 a 35 câmeras por unidade. Para 100 câmeras com reserva, seriam de 4 a 5 unidades.
- **Limitações:** sem ECC, sem RAID e sem fonte redundante. As evidências precisariam de um servidor central. O preço é só sob cotação.

**Recomendação:** rack 4U central. A opção de borda só compensa se o cabeamento até a sala técnica for um problema.

## Cuidados para a montagem própria

1. **Ambiente:** o 4U opera de 0 °C a 40 °C. Numa fábrica de vidro, instale numa sala climatizada ou num rack fechado IP54 com ar-condicionado próprio. Esse é o principal fator de confiabilidade.
2. **Burn-in de 72 horas** antes de colocar em produção: teste de memória, estresse de CPU e GPU, e o `benchmarks/gpu_load_test.py e2e` com 100 câmeras.
3. **Software:** Ubuntu LTS com espelho ZFS, monitoramento pelo BMC (temperatura, ventoinhas, fonte e erros de ECC) e alertas no Grafana.
4. **Use a linha PRO da NVIDIA, não GeForce:** ela tem memória com ECC, ventoinha blower e licença de driver que permite uso em servidor.
5. **Garantias:** ficam por componente (de 3 a 5 anos). Documente os números de série e os contatos de RMA.

## Fontes

- [Advantech – ACP-4340 4U](https://buy.advantech.com/Rackmount-Systems/Industrial-Computers-Rackmount-Chassis-By-Height-4U/model-ACP-4340MB-00XE.htm)
- [SHI – ACP-4340BP-70ZE](https://www.shi.com/product/39292660)
- [L-Tron – ACP-4340MB-00XE](https://www.l-trondirect.com/Advantech/ACP-4340MB-00XE)
- [Newegg – ASRock Rack B650D4U-2L2T/BCM](https://www.newegg.com/asrock-rack-b650d4u-2l2t-bcm-amd-ryzen-7000-series-processors/p/N82E16813140099)
- [Tech-America – B650D4U-2L2T/BCM](https://www.tech-america.com/item/asrock-rack-b650d4u-2l2t-bcm-server-motherboard/b650d4u-2l2t-bcm)
- [Micro Center – RTX PRO 4000 Blackwell](https://www.microcenter.com/product/711670/nvidia-geforce-rtx-pro-4000-blackwell-single-fan-ai-workstation-graphics-card-(oem))
- [Gpuprix – preço RTX PRO 4000 Blackwell](https://gpuprix.com/us/gpus/rtx-pro-4000-blackwell)
- [heise – RTX PRO 4000 SFF](https://heise.de/-10518592)
- [HMC Tech – RTX PRO 4000 SFF specs](https://hmc-tech.com/gpus/nvidia-rtx-pro-4000-blackwell-sff)
- [Neousys – Nuvo-9160GC](https://www.neousys-tech.com/en/product/processor/intel-ipc/intel-14th-13th-12th-gen-core/nuvo-9160gc-intel-12th-gpu-computing-platform)
- [Neousys – Nuvo-9166GC](https://www.neousys-tech.com/en/product/processor/gpu-computing/nuvo-9166gc-intel-13th-l4-gpu-computing-platform/product/compare)
- [Capital & Compute – preços de memória](https://capitalandcompute.net/memory-prices/server/)
- [Newegg – HDD 8 TB enterprise](https://www.newegg.com/p/pl?N=100011695+601356784)
- [Brasil61 – dólar em 06/11/2026](https://brasil61.com/n/dolar-sobe-0-44-e-fecha-a-sexta-feira-cotado-a-r-5-52-bras2617439)
