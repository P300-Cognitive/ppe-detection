# Épico 6 — Alertas e Evidências

## US-013 — Exibir alerta visual {#us-013}

**Contrato**: `specs/contracts/renderer.yaml`

- Pessoa em alerta: bbox vermelha espessa + banner inferior com motivo.
- Pessoa conforme: bbox verde.

```gherkin
Cenário: AC-013-1 — Destaque vermelho em alerta
  Dado PersonCompliance com alert=true
  Quando render() é executado
  Então a bbox da pessoa usa alert_color
```

---

## US-014 — Registrar imagem da ocorrência {#us-014}

**Contrato**: `specs/contracts/renderer.yaml` (EvidencePort)

```gherkin
Cenário: AC-014-1 — Salvar JPEG com timestamp
  Dado um frame e alerta confirmado
  Quando save_evidence() é chamado
  Então cria arquivo .jpg em output_dir com timestamp no nome
```

---

## US-015 — Registrar vídeo da ocorrência {#us-015}

**Contrato**: `specs/contracts/evidence.yaml` (VideoEvidencePort)

Buffer circular com N segundos antes do alerta + M segundos depois.

```gherkin
Cenário: AC-015-1 — Vídeo contém período pré-alerta
  Dado video_pre_seconds=2 e buffer com 2s de frames
  Quando on_alert() é disparado
  Então o vídeo salvo inclui frames do buffer

Cenário: AC-015-2 — Vídeo contém período pós-alerta
  Dado video_post_seconds=1 e video_fps=10
  Quando tick() recebe 10 frames após alerta
  Então finaliza gravação com frames pós-alerta
```

---

## US-016 — Enviar notificação automática {#us-016}

**Status**: specified — não implementado.

Adapters: Telegram, e-mail.
