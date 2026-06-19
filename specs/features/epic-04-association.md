# Épico 4 — Associação Pessoa x EPI

## US-008 — Associar capacete a uma pessoa {#us-008}

**Contrato**: `specs/contracts/association.yaml`

### Região anatômica

Capacete deve ter centro dentro da `head_region` (topo 25% da bbox da pessoa).

```gherkin
Cenário: AC-008-1 — Capacete na cabeça associa corretamente
  Dado uma pessoa em (100, 100, 200, 300)
  E um capacete com centro em (150, 120)
  Quando associate(person, [helmet], "helmet") é chamado
  Então deve retornar o capacete

Cenário: AC-008-2 — Capacete longe não associa
  Dado uma pessoa em (100, 100, 200, 300)
  E um capacete com centro em (400, 120) perto de outra área
  Quando associate(person, [helmet], "helmet") é chamado
  Então deve retornar lista vazia
```

---

## US-009 — Associar colete a uma pessoa {#us-009}

**Contrato**: `specs/contracts/association.yaml`

### Região anatômica

Colete deve estar na `torso_region` (20%-65% da altura da pessoa).

```gherkin
Cenário: AC-009-1 — Colete no tronco associa
  Dado uma pessoa em (100, 100, 200, 300)
  E um colete com centro em (150, 180)
  Quando associate(person, [vest], "vest") é chamado
  Então deve retornar o colete

Cenário: AC-009-2 — Colete na cabeça não associa como colete
  Dado um item "Safety Vest" com centro na head_region
  Quando associate(person, [vest], "vest") é chamado
  Então pode não associar se centro estiver fora da torso_region
```
