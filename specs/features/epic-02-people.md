# Épico 2 — Detecção de Pessoas

## US-003 — Detectar pessoas na imagem {#us-003}

**Contrato**: `specs/contracts/detector.yaml`

### Comportamento

- YOLO detecta classe `Person` (configurável em `classes.person`).
- Cada detecção retorna `BoundingBox` com label e confidence.
- Renderer desenha caixa delimitadora (delegado ao RendererPort).

```gherkin
Cenário: AC-003-1 — Parsear detecções de pessoa
  Dado um resultado YOLO com box cls=Person
  Quando detect() parseia o resultado
  Então a pessoa deve estar em FrameDetections.persons
```

---

## US-004 — Rastrear pessoas entre quadros {#us-004}

**Contrato**: `specs/contracts/detector.yaml`

### Comportamento

- Com `tracking.enabled=true`, cada pessoa recebe `track_id` persistente via ByteTrack.
- IDs distintos para pessoas distintas no mesmo frame.

```gherkin
Cenário: AC-004-1 — Tracking habilitado
  Dado tracking.enabled=true
  Quando detect() é executado em sequência
  Então boxes de pessoa devem incluir track_id quando o tracker atribuir ID
```
