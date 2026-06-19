# Épico 7 — Dashboard e Monitoramento

## US-017 — Visualizar câmeras em tempo real {#us-017}

**Contrato**: `specs/contracts/dashboard.yaml`

```gherkin
Cenário: AC-017-1 — Painel com múltiplas câmeras
  Dado config/cameras.yaml com 2 câmeras
  Quando o dashboard é iniciado
  Então GET /api/cameras retorna lista com ambas

Cenário: AC-017-2 — Alertas em tempo real
  Dado uma ocorrência registrada
  Quando o cliente consulta GET /api/alerts/recent
  Então a ocorrência aparece na resposta
```

---

## US-018 — Consultar histórico de ocorrências {#us-018}

**Contrato**: `specs/contracts/storage.yaml`

```gherkin
Cenário: AC-018-1 — Filtro por data
  Dado ocorrências em datas distintas
  Quando search(from_date, to_date) é chamado
  Então retorna apenas ocorrências no intervalo

Cenário: AC-018-2 — Filtro por câmera
  Quando search(camera_id="cam1") é chamado
  Então retorna apenas ocorrências da câmera cam1

Cenário: AC-018-3 — Filtro por tipo de EPI
  Quando search(ppe_type="helmet") é chamado
  Então retorna ocorrências com capacete ausente
```

---

## US-019 — Gerar relatórios {#us-019}

**Contrato**: `specs/contracts/dashboard.yaml`

```gherkin
Cenário: AC-019-1 — Indicadores por período
  Dado ocorrências no período
  Quando generate_report(from, to) é chamado
  Então retorna total_infractions e compliance_rate

Cenário: AC-019-2 — Exportação Excel
  Quando export_report(format="xlsx") é chamado
  Então cria arquivo .xlsx válido

Cenário: AC-019-3 — Exportação PDF
  Quando export_report(format="pdf") é chamado
  Então cria arquivo .pdf válido
```
