# Spec-Driven Design — PPE Detection

Este projeto segue **Spec-Driven Design (SDD)**: toda funcionalidade nasce de uma especificação formal, é implementada contra contratos definidos e validada por testes de aceitação rastreáveis.

## Fluxo de trabalho

```
histories.md  →  specs/features/  →  specs/contracts/  →  src/  →  tests/spec/
   (negócio)       (comportamento)      (interfaces)      (código)   (aceitação)
```

1. **História de usuário** (`histories.md`) — requisito de negócio em linguagem natural.
2. **Feature spec** (`specs/features/`) — comportamento detalhado, cenários Given/When/Then e critérios mensuráveis.
3. **Contrato** (`specs/contracts/`) — interfaces, tipos de dados e invariantes que o código deve respeitar.
4. **Implementação** (`src/ppe_detection/`) — código que implementa os contratos (`contracts/ports.py`).
5. **Testes de aceitação** (`tests/spec/`) — validam os cenários da spec; cada teste referencia um ID (`US-xxx`, `AC-xxx`).

## Estrutura

| Caminho | Propósito |
|---------|-----------|
| `specs/constitution.md` | Princípios imutáveis do projeto |
| `specs/architecture.md` | Arquitetura e pipeline de dados |
| `specs/manifest.yaml` | Rastreabilidade história → spec → teste → módulo |
| `specs/contracts/` | Contratos de interface (YAML + Python Protocols) |
| `specs/features/` | Especificações por épico |
| `src/ppe_detection/contracts/` | Protocols Python derivados dos contratos |
| `src/ppe_detection/domain/` | Modelos de domínio compartilhados |
| `tests/spec/` | Testes de aceitação |

## Status de implementação

Consulte `specs/manifest.yaml` para o status de cada user story:

- `specified` — spec escrita, sem implementação
- `implemented` — código existe
- `verified` — testes de aceitação passando

## Como adicionar uma feature

1. Escreva ou atualize a user story em `histories.md`.
2. Crie/atualize `specs/features/epic-XX-*.md` com cenários de aceitação.
3. Defina ou estenda contratos em `specs/contracts/`.
4. Implemente `Protocol` correspondente em `src/ppe_detection/contracts/ports.py`.
5. Escreva testes em `tests/spec/test_usXXX_*.py` com marker `@pytest.mark.spec("US-XXX")`.
6. Atualize `specs/manifest.yaml`.
7. Execute: `pytest tests/spec/ -v`

## Comandos

```bash
# Instalar com dependências de dev
pip install -e ".[dev]"

# Rodar testes de aceitação (specs)
pytest tests/spec/ -v

# Rodar aplicação
ppe-detection --source 0
```
