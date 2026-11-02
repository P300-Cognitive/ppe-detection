"""Dashboard web Flask: streaming MJPEG, alertas, histórico, relatórios e admin."""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import TYPE_CHECKING

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, send_file

if TYPE_CHECKING:
    from src.dashboard.state import AppState


# ── HTML do dashboard ─────────────────────────────────────────────────────────

_HTML = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PPE Detection – Dashboard</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0d1117;--surface:#161b22;--surface2:#21262d;
    --accent:#f85149;--green:#3fb950;--yellow:#d29922;
    --text:#c9d1d9;--dim:#8b949e;--border:#30363d;
    --radius:8px;
  }
  body{background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;font-size:14px}
  header{
    display:flex;align-items:center;justify-content:space-between;
    padding:12px 20px;background:var(--surface);border-bottom:1px solid var(--border);
  }
  header h1{font-size:1.1rem;display:flex;align-items:center;gap:8px}
  #alert-badge{
    background:var(--accent);color:#fff;border-radius:12px;
    padding:2px 10px;font-size:.8rem;font-weight:700;min-width:28px;text-align:center;
  }
  #alert-badge.zero{background:var(--green)}
  .main{display:grid;grid-template-columns:1fr 340px;gap:0;height:calc(100vh - 49px - 40px)}
  .video-panel{background:#000;display:flex;align-items:center;justify-content:center;overflow:hidden}
  .video-panel img{width:100%;height:100%;object-fit:contain}
  .side-panel{background:var(--surface);border-left:1px solid var(--border);display:flex;flex-direction:column}
  .side-panel h2{padding:12px 16px;font-size:.85rem;color:var(--dim);text-transform:uppercase;
    letter-spacing:.08em;border-bottom:1px solid var(--border)}
  #alert-list{flex:1;overflow-y:auto;padding:8px}
  .alert-item{
    background:var(--surface2);border:1px solid var(--border);border-left:3px solid var(--accent);
    border-radius:var(--radius);padding:10px 12px;margin-bottom:8px;
  }
  .alert-item .who{font-weight:600;color:var(--accent)}
  .alert-item .meta{color:var(--dim);font-size:.8rem;margin-top:4px}
  .no-alerts{color:var(--dim);text-align:center;padding:24px;font-size:.9rem}
  nav.tabs{
    display:flex;background:var(--surface);border-top:1px solid var(--border);
    height:40px;
  }
  nav.tabs button{
    flex:1;background:none;border:none;color:var(--dim);cursor:pointer;
    font-size:.85rem;border-bottom:2px solid transparent;transition:all .15s;
  }
  nav.tabs button.active{color:var(--text);border-bottom-color:var(--accent)}
  nav.tabs button:hover{color:var(--text)}
  .tab-content{display:none;padding:16px;overflow-y:auto;max-height:calc(100vh - 49px - 40px - 200px)}
  .tab-content.active{display:block}
  .form-row{display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
  .form-row label{color:var(--dim);min-width:80px;font-size:.8rem}
  input,select{
    background:var(--surface2);border:1px solid var(--border);color:var(--text);
    padding:6px 10px;border-radius:var(--radius);font-size:.85rem;outline:none;
  }
  input:focus,select:focus{border-color:var(--accent)}
  button.btn{
    background:var(--accent);color:#fff;border:none;padding:6px 14px;
    border-radius:var(--radius);cursor:pointer;font-size:.85rem;
  }
  button.btn-ghost{
    background:var(--surface2);color:var(--text);border:1px solid var(--border);
    padding:6px 14px;border-radius:var(--radius);cursor:pointer;font-size:.85rem;
  }
  button.btn:hover{opacity:.85} button.btn-ghost:hover{border-color:var(--accent)}
  table{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:8px}
  table th{color:var(--dim);text-align:left;padding:6px 8px;border-bottom:1px solid var(--border)}
  table td{padding:6px 8px;border-bottom:1px solid var(--border)}
  table tr:hover td{background:var(--surface2)}
  .tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.75rem;font-weight:600}
  .tag-red{background:#3d1f22;color:var(--accent)}
  .tag-green{background:#1a3524;color:var(--green)}
  .kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
  .kpi{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px}
  .kpi .value{font-size:1.8rem;font-weight:700;color:var(--accent)}
  .kpi .label{color:var(--dim);font-size:.78rem;margin-top:4px}
  .threshold-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
  .threshold-row label{min-width:80px;color:var(--dim);font-size:.85rem}
  .threshold-row input[type=range]{flex:1;accent-color:var(--accent)}
  .threshold-row .val{min-width:36px;text-align:right;font-weight:600}
  #report-kpis{margin-bottom:16px}
  .sep{height:1px;background:var(--border);margin:14px 0}
</style>
</head>
<body>
<header>
  <h1>&#x1F9BA; PPE Detection</h1>
  <div style="display:flex;align-items:center;gap:12px">
    <span style="color:var(--dim);font-size:.8rem" id="status-text">Conectando...</span>
    <span id="alert-badge" class="zero">0</span>
  </div>
</header>

<div class="main">
  <div class="video-panel">
    <img src="/video_feed" alt="Camera feed">
  </div>
  <div class="side-panel">
    <h2>Alertas Ativos</h2>
    <div id="alert-list"><p class="no-alerts">Nenhum alerta.</p></div>
  </div>
</div>

<nav class="tabs">
  <button class="active" onclick="showTab('history')">Histórico</button>
  <button onclick="showTab('thresholds')">Limiares</button>
  <button onclick="showTab('report')">Relatório</button>
  <button onclick="showTab('admin')">Admin</button>
</nav>

<!-- HISTÓRICO -->
<div id="tab-history" class="tab-content active">
  <div class="form-row">
    <label>Data</label>
    <input type="date" id="h-date">
    <label>Câmera</label>
    <input type="text" id="h-cam" placeholder="CAM-01" style="width:90px">
    <label>EPI</label>
    <input type="text" id="h-ppe" placeholder="helmet" style="width:80px">
    <button class="btn" onclick="loadHistory()">Filtrar</button>
  </div>
  <table>
    <thead><tr><th>Pessoa</th><th>Câmera</th><th>Motivo</th><th>Data/Hora</th></tr></thead>
    <tbody id="history-body"><tr><td colspan="4" style="color:var(--dim);text-align:center">Carregando...</td></tr></tbody>
  </table>
</div>

<!-- LIMIARES -->
<div id="tab-thresholds" class="tab-content">
  <p style="color:var(--dim);margin-bottom:14px;font-size:.85rem">
    Ajuste a sensibilidade da detecção por classe de EPI. Valores entre 0.1 e 1.0.
  </p>
  <div id="threshold-rows"></div>
  <button class="btn" onclick="saveThresholds()">Salvar Limiares</button>
</div>

<!-- RELATÓRIO -->
<div id="tab-report" class="tab-content">
  <div class="form-row">
    <label>De</label>
    <input type="date" id="r-start">
    <label>Até</label>
    <input type="date" id="r-end">
    <button class="btn" onclick="loadReport()">Gerar</button>
  </div>
  <div id="report-kpis" class="kpi-grid" style="display:none">
    <div class="kpi"><div class="value" id="r-violations">–</div><div class="label">Infrações</div></div>
    <div class="kpi"><div class="value" id="r-compliance" style="color:var(--green)">–</div><div class="label">Conformidade</div></div>
  </div>
  <div class="form-row">
    <button class="btn-ghost" onclick="downloadReport('pdf')">&#x2B07; PDF</button>
    <button class="btn-ghost" onclick="downloadReport('excel')">&#x2B07; Excel</button>
  </div>
</div>

<!-- ADMIN -->
<div id="tab-admin" class="tab-content">
  <p style="color:var(--dim);font-size:.85rem;margin-bottom:12px">Câmeras cadastradas</p>
  <div class="form-row">
    <input type="text" id="new-rtsp" placeholder="rtsp://192.168.1.x/stream" style="flex:1">
    <button class="btn" onclick="registerCamera()">Adicionar</button>
  </div>
  <table>
    <thead><tr><th>ID</th><th>URL RTSP</th><th>Status</th></tr></thead>
    <tbody id="cam-body"></tbody>
  </table>
</div>

<script>
const PPE_CLASSES = ["helmet","vest","glasses","mask","gloves","boots"];
let thresholdValues = {};
let reportPeriod = {start:"", end:""};

// ── Inicialização ────────────────────────────────────────────────────────────
window.onload = () => {
  const today = new Date().toISOString().slice(0,10);
  const first = today.slice(0,8)+"01";
  document.getElementById("r-start").value = first;
  document.getElementById("r-end").value   = today;
  document.getElementById("h-date").value  = today;
  loadAlerts();
  loadHistory();
  loadThresholds();
  loadCameras();
  setInterval(loadAlerts, 2000);
};

// ── Tabs ─────────────────────────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll("nav.tabs button").forEach(b => b.classList.remove("active"));
  document.getElementById("tab-"+name).classList.add("active");
  event.target.classList.add("active");
  if (name === "history")    loadHistory();
  if (name === "thresholds") loadThresholds();
  if (name === "admin")      loadCameras();
}

// ── Alertas ──────────────────────────────────────────────────────────────────
function loadAlerts() {
  fetch("/api/alerts")
    .then(r => r.json())
    .then(data => {
      const badge = document.getElementById("alert-badge");
      const list  = document.getElementById("alert-list");
      badge.textContent = data.length;
      badge.className   = data.length > 0 ? "" : "zero";
      document.getElementById("status-text").textContent = "Ao vivo";
      if (data.length === 0) {
        list.innerHTML = "<p class='no-alerts'>Nenhum alerta ativo.</p>";
        return;
      }
      list.innerHTML = data.map(a => {
        const ts = a.timestamp ? new Date(a.timestamp).toLocaleTimeString("pt-BR") : "–";
        return "<div class='alert-item'>" +
          "<div class='who'>Pessoa " + a.person_id + " &mdash; " +
          "<span class='tag tag-red'>" + (a.ppe_type||a.reason||"–") + "</span></div>" +
          "<div class='meta'>" + (a.camera_id||"") + " &bull; " + ts + "</div></div>";
      }).join("");
    })
    .catch(() => document.getElementById("status-text").textContent = "Sem conexão");
}

// ── Histórico ────────────────────────────────────────────────────────────────
function loadHistory() {
  const date   = document.getElementById("h-date").value;
  const cam    = document.getElementById("h-cam").value.trim();
  const ppe    = document.getElementById("h-ppe").value.trim();
  let url = "/api/history?";
  if (date) url += "date=" + date + "&";
  if (cam)  url += "camera_id=" + cam + "&";
  if (ppe)  url += "ppe_type=" + ppe;
  fetch(url)
    .then(r => r.json())
    .then(data => {
      const body = document.getElementById("history-body");
      if (!data.length) {
        body.innerHTML = "<tr><td colspan='4' style='color:var(--dim);text-align:center'>Nenhuma ocorrência encontrada.</td></tr>";
        return;
      }
      body.innerHTML = data.map(i => {
        const ts = i.timestamp ? new Date(i.timestamp).toLocaleString("pt-BR") : "–";
        return "<tr><td>Pessoa " + (i.person_id||"–") + "</td><td>" + (i.camera_id||"–") +
          "</td><td><span class='tag tag-red'>" + (i.reason||i.ppe_type||"–") +
          "</span></td><td>" + ts + "</td></tr>";
      }).join("");
    });
}

// ── Limiares ─────────────────────────────────────────────────────────────────
function loadThresholds() {
  fetch("/api/thresholds")
    .then(r => r.json())
    .then(data => {
      thresholdValues = data;
      const container = document.getElementById("threshold-rows");
      container.innerHTML = PPE_CLASSES.map(cls => {
        const val = (data[cls] !== undefined ? data[cls] : 0.5).toFixed(2);
        return "<div class='threshold-row'>" +
          "<label>" + cls + "</label>" +
          "<input type='range' min='0.1' max='1' step='0.05' value='" + val +
          "' id='th-" + cls + "' oninput=\"document.getElementById('th-v-" + cls + "').textContent=parseFloat(this.value).toFixed(2)\">" +
          "<span class='val' id='th-v-" + cls + "'>" + val + "</span></div>";
      }).join("");
    });
}

function saveThresholds() {
  const promises = PPE_CLASSES.map(cls => {
    const el = document.getElementById("th-" + cls);
    if (!el) return Promise.resolve();
    return fetch("/api/thresholds", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({class: cls, value: parseFloat(el.value)})
    });
  });
  Promise.all(promises).then(() => {
    const btn = event.target;
    btn.textContent = "Salvo!";
    setTimeout(() => btn.textContent = "Salvar Limiares", 1500);
  });
}

// ── Relatório ────────────────────────────────────────────────────────────────
function loadReport() {
  const start = document.getElementById("r-start").value;
  const end   = document.getElementById("r-end").value;
  if (!start || !end) return;
  reportPeriod = {start, end};
  fetch("/api/report?start=" + start + "&end=" + end)
    .then(r => r.json())
    .then(data => {
      document.getElementById("report-kpis").style.display = "grid";
      document.getElementById("r-violations").textContent = data.total_violations;
      document.getElementById("r-compliance").textContent = data.compliance_rate.toFixed(1) + "%";
    });
}

function downloadReport(fmt) {
  if (!reportPeriod.start) { loadReport(); return; }
  window.location = "/api/report/" + fmt + "?start=" + reportPeriod.start + "&end=" + reportPeriod.end;
}

// ── Admin / Câmeras ───────────────────────────────────────────────────────────
function loadCameras() {
  fetch("/api/cameras")
    .then(r => r.json())
    .then(data => {
      const body = document.getElementById("cam-body");
      if (!data.length) {
        body.innerHTML = "<tr><td colspan='3' style='color:var(--dim);text-align:center'>Nenhuma câmera cadastrada.</td></tr>";
        return;
      }
      body.innerHTML = data.map(c =>
        "<tr><td>" + c.id + "</td><td style='font-size:.8rem;color:var(--dim)'>" + c.rtsp_url +
        "</td><td><span class='tag " + (c.enabled ? "tag-green" : "tag-red") + "'>" +
        (c.enabled ? "Ativo" : "Inativo") + "</span></td></tr>"
      ).join("");
    });
}

function registerCamera() {
  const url = document.getElementById("new-rtsp").value.trim();
  if (!url) return;
  fetch("/api/cameras", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({rtsp_url: url})
  }).then(r => r.json()).then(() => {
    document.getElementById("new-rtsp").value = "";
    loadCameras();
  });
}
</script>
</body>
</html>
"""


# ── Factory Flask ─────────────────────────────────────────────────────────────

def create_app(state: "AppState") -> Flask:
    app = Flask(__name__)
    app.config["state"] = state

    def _s() -> "AppState":
        return app.config["state"]

    # ── MJPEG stream ──────────────────────────────────────────────────────

    def _frames():
        while True:
            frame = _s().get_frame()
            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    frame, "Aguardando camera...", (160, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (80, 80, 80), 2,
                )
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
            time.sleep(1 / 15)

    @app.route("/video_feed")
    def video_feed():
        return Response(_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    # ── Alertas ───────────────────────────────────────────────────────────

    @app.route("/api/alerts")
    def api_alerts():
        return jsonify([
            {
                "person_id": a.person_id,
                "ppe_type":  a.ppe_type,
                "camera_id": a.camera_id,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in _s().monitor.get_active_alerts()
        ])

    # ── Histórico ─────────────────────────────────────────────────────────

    @app.route("/api/history")
    def api_history():
        date      = request.args.get("date")
        camera_id = request.args.get("camera_id")
        ppe_type  = request.args.get("ppe_type")
        items = _s().history.filter(date=date, camera_id=camera_id, ppe_type=ppe_type)
        return jsonify([
            {
                "person_id": getattr(i, "person_id", None),
                "camera_id": getattr(i, "camera_id", None),
                "reason":    getattr(i, "reason", getattr(i, "ppe_type", None)),
                "timestamp": (
                    getattr(i, "timestamp", datetime.now()).isoformat()
                    if hasattr(i, "timestamp") else None
                ),
            }
            for i in items
        ])

    # ── Limiares ──────────────────────────────────────────────────────────

    @app.route("/api/thresholds", methods=["GET"])
    def api_get_thresholds():
        return jsonify(_s().threshold_manager.get_all())

    @app.route("/api/thresholds", methods=["POST"])
    def api_set_threshold():
        data = request.get_json() or {}
        cls  = data.get("class")
        val  = data.get("value")
        if not cls or val is None:
            return jsonify({"error": "Campos 'class' e 'value' obrigatórios"}), 400
        try:
            _s().threshold_manager.set(cls, float(val))
            return jsonify({"ok": True, "class": cls, "value": float(val)})
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 422

    # ── Câmeras ───────────────────────────────────────────────────────────

    @app.route("/api/cameras", methods=["GET"])
    def api_cameras():
        return jsonify([
            {"id": c.id, "rtsp_url": c.rtsp_url, "enabled": c.enabled}
            for c in _s().cam_manager.list_all()
        ])

    @app.route("/api/cameras", methods=["POST"])
    def api_register_camera():
        data = request.get_json() or {}
        rtsp_url = data.get("rtsp_url")
        if not rtsp_url:
            return jsonify({"error": "'rtsp_url' obrigatório"}), 400
        cam = _s().cam_manager.register(rtsp_url)
        return jsonify({"id": cam.id, "rtsp_url": cam.rtsp_url}), 201

    # ── Relatório ─────────────────────────────────────────────────────────

    @app.route("/api/report")
    def api_report():
        from src.reports.generator import ReportGenerator
        start = request.args.get("start", datetime.now().strftime("%Y-%m-01"))
        end   = request.args.get("end",   datetime.now().strftime("%Y-%m-%d"))
        rpt   = ReportGenerator().generate(start=start, end=end)
        return jsonify({
            "start": rpt.start, "end": rpt.end,
            "total_violations": rpt.total_violations,
            "compliance_rate":  rpt.compliance_rate,
        })

    @app.route("/api/report/pdf")
    def api_report_pdf():
        from src.reports.generator import ReportGenerator
        start = request.args.get("start", datetime.now().strftime("%Y-%m-01"))
        end   = request.args.get("end",   datetime.now().strftime("%Y-%m-%d"))
        gen   = ReportGenerator()
        path  = gen.export_pdf(gen.generate(start=start, end=end))
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))

    @app.route("/api/report/excel")
    def api_report_excel():
        from src.reports.generator import ReportGenerator
        start = request.args.get("start", datetime.now().strftime("%Y-%m-01"))
        end   = request.args.get("end",   datetime.now().strftime("%Y-%m-%d"))
        gen   = ReportGenerator()
        path  = gen.export_excel(gen.generate(start=start, end=end))
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))

    # ── HTML ──────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        return Response(_HTML, mimetype="text/html; charset=utf-8")

    return app
