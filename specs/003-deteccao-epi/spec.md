# Spec 003: Detecção de EPI

**Status:** retroativa | **Histórias:** US-005, US-006, US-007 | **Cenários:** [`features/epic3_deteccao_epi/`](../../features/epic3_deteccao_epi/)

## Contexto

O sistema precisa reconhecer equipamentos de proteção na imagem para que as regras de segurança possam avaliar a conformidade. A qualidade desta etapa depende de um modelo treinado com as classes de EPI, que **ainda não existe no repositório**.

## Histórias de usuário

**US-005 – Detectar capacetes.** Como responsável pela segurança, quero identificar capacetes na imagem, para que o sistema valide o uso correto do EPI.

**US-006 – Detectar coletes refletivos.** Como responsável pela segurança, quero identificar coletes refletivos, para que o sistema valide a conformidade dos trabalhadores.

**US-007 – Detectar outros EPIs.** Como responsável pela segurança, quero detectar óculos, máscaras, luvas e botas, para que a inspeção seja mais completa.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Detectar capacetes com caixa delimitadora | US-005 | Não verificado | Código pronto; falta modelo treinado |
| FR-002 | Exibir a confiança junto à caixa | US-005 | Atendido | No fluxo de produção e em `render` |
| FR-003 | Detectar capacetes amarelos, brancos e azuis | US-005 | Não verificado | Depende do treinamento do modelo |
| FR-004 | Detectar coletes de qualquer cor | US-006 | Não verificado | Depende do treinamento do modelo |
| FR-005 | Associar o colete à pessoa correta | US-006 | Atendido | Feito na [spec 004](../004-associacao-pessoa-epi/spec.md). O cenário daqui só conta detecções |
| FR-006 | Detectar óculos, máscaras, luvas e botas individualmente | US-007 | Não verificado | Código pronto; falta modelo treinado. O cenário nunca passaria, conforme o plano |
| FR-007 | Informar quais EPIs foram encontrados para cada pessoa | US-007 | Parcial | A associação existe só internamente, não é exibida, e os quatro EPIs da US-007 nunca são associados |

## Casos de borda

- Modelo não fornecido: o detector retorna lista vazia sem nenhum aviso. Ver [009/FR-005](../009-orquestracao-plataforma/spec.md).
- Modelo com outras classes: o mapeamento de nomes precisa ser informado, ou as classes ficam incorretas.
- Arquivo de modelo inválido: a falha ocorre ao carregar o modelo.

## Critérios de sucesso

- Existe um modelo treinado com as seis classes e com métricas registradas por classe.
- Os cenários passam com imagens reais de cada EPI.
- Cada cor de capacete listada é detectada em imagens de teste.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] De onde vem o modelo: treinamento próprio ou pesos de terceiros? Com qual conjunto de dados e qual licença?
- [NEEDS CLARIFICATION] Qual a precisão e a sensibilidade mínimas por classe para aceitar um modelo?
