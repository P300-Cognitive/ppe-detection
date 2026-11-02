# Spec 004: Associação entre pessoa e EPI

**Status:** retroativa | **Histórias:** US-008, US-009 | **Cenários:** [`features/epic4_associacao_pessoa_epi/`](../../features/epic4_associacao_pessoa_epi/)

## Contexto

Detectar um EPI na imagem não basta: é preciso saber quem o está usando. Sem essa ligação, uma pessoa sem capacete ao lado de outra com capacete não seria identificada corretamente.

## Histórias de usuário

**US-008 – Associar capacete a uma pessoa.** Como responsável pela segurança, quero relacionar cada capacete à pessoa correspondente, para que seja possível detectar ausência de proteção.

**US-009 – Associar colete a uma pessoa.** Como responsável pela segurança, quero relacionar cada colete à pessoa correspondente, para que seja possível validar o uso correto do equipamento.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Associar o capacete à pessoa cuja cabeça está sob ele | US-008 | Atendido | Testado com caixas sintéticas |
| FR-002 | Não associar o capacete a uma pessoa próxima | US-008 | Atendido | Pessoas lado a lado, sem sobreposição. Falta testar com sobreposição |
| FR-003 | Associar o colete à pessoa cujo tronco está sobreposto a ele | US-009 | Atendido | Testado com caixas sintéticas |
| FR-004 | Não associar o colete a uma pessoa próxima | US-009 | Atendido | Mesma ressalva do FR-002 |
| FR-005 | Associar óculos, máscaras, luvas e botas à pessoa correta | US-007 | Não atendido | Com tamanhos realistas, esses EPIs nunca são associados. Exigi-los gera alerta para todos |

## Casos de borda

- Pessoas sobrepostas: o EPI vai para a pessoa de maior sobreposição, o que pode estar errado.
- EPI pequeno em relação à região do corpo: pode ficar abaixo do limite e não ser associado.
- Dois capacetes sobre a mesma pessoa: ambos são associados a ela.
- EPI no chão ou em uma mesa: não é associado, desde que não sobreponha ninguém.

## Critérios de sucesso

- As seis classes são associadas corretamente em imagens de teste com tamanhos realistas.
- Com duas pessoas parcialmente sobrepostas, o EPI fica com quem o usa.
- Um EPI fora do corpo não é associado a ninguém.
