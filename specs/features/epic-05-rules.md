# Épico 5 — Regras de Segurança

## US-010 — Identificar ausência de capacete {#us-010}

**Contrato**: `specs/contracts/rules.yaml`

```gherkin
Cenário: AC-010-1 — Alerta após confirmação
  Dado confirmation_frames=3 e required_ppe=[helmet]
  E uma pessoa sem capacete por 3 frames consecutivos
  Quando evaluate() é chamado no 3º frame
  Então alert=true e alert_reason contém "Capacete"

Cenário: AC-010-2 — Sem alerta antes da confirmação
  Dado confirmation_frames=5
  E ausência de capacete por apenas 2 frames
  Quando evaluate() é chamado
  Então alert=false
```

---

## US-011 — Identificar ausência de colete {#us-011}

Mesma lógica de confirmação temporal, aplicada a `vest`.

---

## US-012 — Configurar regras por ambiente {#us-012}

- `rules.required_ppe` definido em `config/default.yaml`.
- CLI `--required-ppe helmet vest` sobrescreve por execução.
- Cada câmera futuramente terá config própria (dashboard — US-020).

```gherkin
Cenário: AC-012-1 — EPIs obrigatórios configuráveis
  Dado required_ppe=[helmet] apenas
  Quando evaluate() analisa pessoa com capacete mas sem colete
  Então alert=false
```
