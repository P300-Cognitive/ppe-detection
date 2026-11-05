"""Dashboard web Flask: streaming MJPEG, alertas, histórico, relatórios e admin."""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import TYPE_CHECKING

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, send_file

from src.dashboard.state import KNOWN_PPE
from src.video.devices import NO_CAMERA, label_for_source, list_local_cameras, parse_source

if TYPE_CHECKING:
    from src.dashboard.state import AppState


# ── HTML do dashboard ─────────────────────────────────────────────────────────

_HTML = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SCHOTT Vision – Monitor de EPI</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#030914;
    --surface:#081426;
    --surface2:#0d1d33;
    --surface3:#102743;
    --ink:#f5f7f8;
    --muted:#8da5bd;
    --line:#193652;
    --accent:#16b8f3;
    --accent-ink:#041018;
    --danger:#ff5d6c;
    --ok:#3dce86;
    --warning:#ffbf5b;
    --radius:14px;
  }
  html,body{height:100%}
  body{
    background:
      radial-gradient(900px 420px at 0% -10%, rgba(7,173,242,.16), transparent 55%),
      var(--bg);
    color:var(--ink);
    font-family:Inter,"Segoe UI",Helvetica,Arial,sans-serif;
    font-size:14px;
    display:flex;
    flex-direction:column;
    overflow:hidden;
  }
  header{
    display:flex;align-items:center;justify-content:space-between;
    min-height:84px;padding:12px 20px;border-bottom:1px solid var(--line);
    background:rgba(1,12,30,.94);backdrop-filter:blur(8px);
    z-index:5;
  }
  .brand{display:flex;align-items:center;gap:14px}
  .logo{
    height:68px;width:auto;object-fit:contain;display:block;border-radius:10px;
    box-shadow:0 0 0 1px rgba(7,173,242,.35), 0 8px 24px rgba(7,173,242,.12);
  }
  .brand h1{font-size:16px;font-weight:700;letter-spacing:-.02em}
  .brand p{color:var(--muted);font-size:12px;margin-top:2px}
  .header-meta{display:flex;align-items:center;gap:10px}
  .live{
    display:flex;align-items:center;gap:8px;
    background:var(--surface2);border:1px solid var(--line);
    border-radius:999px;padding:6px 12px;color:var(--muted);font-size:12px;
  }
  .live-dot{
    width:8px;height:8px;border-radius:50%;background:var(--ok);
    box-shadow:0 0 0 0 rgba(61,206,134,.65);animation:pulse 1.8s infinite;
  }
  .live-dot.off{background:var(--danger);animation:none;box-shadow:none}
  @keyframes pulse{
    70%{box-shadow:0 0 0 7px rgba(61,206,134,0)}
  }
  #alert-badge{
    min-width:36px;text-align:center;font-weight:750;font-size:13px;
    background:var(--danger);color:#fff;border-radius:999px;padding:6px 10px;
  }
  #alert-badge.zero{background:#0b4d8b;color:#d7f3ff}
  .icon-btn{
    width:34px;height:34px;display:grid;place-items:center;border-radius:10px;
    background:var(--surface2);border:1px solid var(--line);color:var(--muted);
    cursor:pointer;font-size:16px;
  }
  .icon-btn:hover{border-color:var(--accent);color:var(--ink)}
  .rules{
    flex:0 0 auto;
    display:flex;align-items:center;gap:12px;flex-wrap:wrap;
    padding:10px 12px;border:1px solid var(--line);border-radius:14px;
    background:rgba(7,20,40,.92);
  }
  .rules-label{
    font-size:11px;letter-spacing:.08em;text-transform:uppercase;
    color:var(--muted);font-weight:700;
  }
  .ppe-picks{display:flex;flex-wrap:wrap;gap:8px}
  .pick{
    background:transparent;border:1px solid var(--line);color:var(--muted);
    border-radius:999px;padding:6px 12px;cursor:pointer;font-size:12px;font-weight:650;
  }
  .pick.on{background:rgba(7,173,242,.16);border-color:var(--accent);color:var(--ink)}
  .pick:hover{border-color:var(--accent);color:var(--ink)}
  .rules-note{margin-left:auto;color:var(--ok);font-size:12px;min-height:1em}
  .shell{
    flex:1;min-height:0;
    display:grid;grid-template-columns:minmax(0,1fr) minmax(340px,400px);
  }
  .stage{min-height:0;display:flex;flex-direction:column;padding:18px;gap:12px;overflow:auto}
  .stage-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}
  .eyebrow{color:var(--accent);font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
  .stage-title{display:flex;align-items:center;gap:10px;margin-top:4px}
  .stage-title h2{font-size:19px;letter-spacing:-.025em}
  .camera-pill{
    padding:3px 8px;border:1px solid var(--line);border-radius:999px;
    color:var(--muted);font-size:11px;font-weight:700;
  }
  .camera-select{display:flex;flex-direction:column;gap:4px;min-width:240px;color:var(--muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase}
  .camera-select select{text-transform:none;letter-spacing:0}
  .cam-list{display:flex;flex-direction:column;gap:8px;margin-bottom:14px}
  .cam-row{
    display:flex;align-items:center;justify-content:space-between;gap:10px;
    background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px 12px;
  }
  .cam-row.on{border-color:rgba(7,173,242,.7)}
  .cam-row strong{display:block;font-size:13px}
  .cam-row .meta{color:var(--muted);font-size:12px;margin-top:2px}
  .quick-stats{display:flex;gap:8px}
  .quick-stat{
    min-width:100px;background:rgba(8,20,38,.72);border:1px solid var(--line);
    border-radius:12px;padding:8px 11px;
  }
  .quick-stat span{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em}
  .quick-stat strong{display:block;margin-top:2px;font-size:15px;font-variant-numeric:tabular-nums}
  .quick-stat.danger strong{color:var(--danger)}
  #clock{font-variant-numeric:tabular-nums;color:var(--ink);font-size:13px;font-weight:700}
  .stage-frame{
    flex:1 1 auto;min-height:240px;background:#020814;border:1px solid var(--line);
    border-radius:18px;overflow:hidden;position:relative;
    box-shadow:0 20px 50px rgba(0,0,0,.28);
  }
  .stage-frame img{width:100%;height:100%;object-fit:contain;display:block}
  .stream-state{
    position:absolute;inset:0;display:none;place-items:center;text-align:center;
    color:var(--muted);background:#020814;z-index:2;
  }
  .stream-state.visible{display:grid}
  .stream-state strong{display:block;color:var(--ink);margin-bottom:5px}
  .frame-bar{
    position:absolute;left:12px;right:12px;bottom:12px;
    display:flex;justify-content:space-between;align-items:center;gap:12px;
    background:rgba(1,12,30,.78);border:1px solid rgba(7,173,242,.28);
    border-radius:12px;padding:8px 12px;backdrop-filter:blur(8px);
  }
  .legend{display:flex;gap:14px;color:var(--muted);font-size:12px;flex-wrap:wrap}
  .legend span{display:flex;align-items:center;gap:6px}
  .swatch{width:8px;height:8px;border-radius:50%}
  .rail{
    min-height:0;display:flex;flex-direction:column;
    background:var(--surface);border-left:1px solid var(--line);
  }
  .panel-head{
    display:flex;align-items:center;justify-content:space-between;
    padding:16px 16px 12px;
  }
  .panel-head h2{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
  .panel-count{
    min-width:25px;height:22px;display:grid;place-items:center;border-radius:7px;
    background:var(--surface2);color:var(--muted);font-size:11px;font-weight:800;
  }
  #alert-list{flex:1;overflow:auto;padding:0 12px 12px}
  .alerts{flex:0 0 auto;max-height:42%;min-height:168px;display:flex;flex-direction:column;border-bottom:1px solid var(--line)}
  .ppe-status{display:grid;grid-template-columns:repeat(auto-fit,minmax(92px,1fr));gap:8px;padding:0 12px 12px}
  .ppe-chip{
    background:var(--surface2);border:1px solid var(--line);border-radius:12px;
    padding:8px 6px;text-align:center;
  }
  .ppe-chip span{display:block;color:var(--muted);font-size:10px;letter-spacing:.06em;text-transform:uppercase}
  .ppe-chip strong{display:block;margin-top:3px;font-size:13px;color:var(--muted)}
  .ppe-chip.good{border-color:rgba(61,206,134,.45)}
  .ppe-chip.good strong{color:var(--ok)}
  .ppe-chip.bad{border-color:rgba(255,93,108,.6);background:#2a1220}
  .ppe-chip.bad strong{color:#ffb4bc}
  .alert-item{
    background:var(--surface2);border:1px solid var(--line);
    border-left:3px solid var(--danger);border-radius:12px;
    padding:11px 12px;margin-bottom:8px;transition:transform .16s,border-color .16s;
  }
  .alert-item:hover{transform:translateY(-1px);border-color:#31506d}
  .alert-top{display:flex;justify-content:space-between;align-items:center;gap:8px}
  .alert-item .who{font-weight:650;margin-top:6px}
  .alert-item .meta{color:var(--muted);font-size:12px;margin-top:2px}
  .no-alerts{color:var(--muted);text-align:center;padding:28px 12px;font-size:13px;line-height:1.5}
  .workspace{flex:1;min-height:0;display:flex;flex-direction:column}
  nav.tabs{display:flex;gap:3px;padding:10px 10px 0;border-bottom:1px solid var(--line)}
  nav.tabs button{
    flex:1;background:transparent;border:none;color:var(--muted);cursor:pointer;
    font-size:11px;font-weight:700;padding:9px 4px;border-radius:9px 9px 0 0;
    border-bottom:2px solid transparent;
  }
  nav.tabs button.active{background:rgba(22,184,243,.06);color:var(--ink);border-bottom-color:var(--accent)}
  nav.tabs button:hover{color:var(--ink)}
  .panels{flex:1;min-height:0;overflow:auto;background:var(--bg)}
  .tab-content{display:none;padding:14px}
  .tab-content.active{display:block}
  .hint{color:var(--muted);font-size:12px;line-height:1.45;margin-bottom:12px}
  .filters{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
  .filters label,.field{display:flex;flex-direction:column;gap:4px;color:var(--muted);font-size:11px;letter-spacing:.04em;text-transform:uppercase}
  .span-2{grid-column:span 2}
  input,select{
    background:var(--surface);border:1px solid var(--line);color:var(--ink);
    padding:8px 10px;border-radius:10px;font-size:13px;outline:none;width:100%;
    text-transform:none;letter-spacing:0;
  }
  input:focus,select:focus{border-color:var(--accent)}
  input::placeholder{color:#60788f}
  button.btn,button.btn-ghost{
    border-radius:10px;padding:8px 14px;cursor:pointer;font-size:13px;font-weight:650;
  }
  button.btn{background:var(--accent);color:var(--accent-ink);border:none}
  button.btn-ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}
  button.btn:hover{filter:brightness(1.08)}
  button.btn-ghost:hover{border-color:var(--accent)}
  .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}
  table{width:100%;border-collapse:collapse;font-size:12px}
  table th{color:var(--muted);text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);font-weight:650}
  table td{padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:middle}
  table tr:hover td{background:rgba(255,255,255,.03)}
  .tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700}
  .tag-red{background:#3a201c;color:#ffb0a6}
  .tag-green{background:#0b4d8b;color:#d7f3ff}
  .kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
  .kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px}
  .kpi .value{font-size:28px;font-weight:750;letter-spacing:-.04em}
  .kpi .label{color:var(--muted);font-size:12px;margin-top:4px}
  .threshold-row{display:flex;align-items:center;gap:10px;margin-bottom:12px}
  .threshold-row label{min-width:78px;color:var(--ink);font-size:13px}
  .threshold-row input[type=range]{flex:1;accent-color:var(--accent)}
  .threshold-row .val{min-width:36px;text-align:right;font-variant-numeric:tabular-nums;font-weight:700}
  .table-wrap{overflow:auto}
  .empty-state{padding:34px 12px;text-align:center;color:var(--muted)}
  .empty-state .empty-icon{font-size:24px;display:block;margin-bottom:8px;opacity:.8}
  .toast{
    position:fixed;right:18px;bottom:18px;z-index:20;max-width:320px;
    background:#102743;border:1px solid #295170;border-radius:12px;padding:11px 14px;
    box-shadow:0 14px 36px rgba(0,0,0,.35);color:var(--ink);
    opacity:0;transform:translateY(8px);pointer-events:none;transition:.2s;
  }
  .toast.show{opacity:1;transform:none}
  .toast.error{border-color:rgba(255,93,108,.65)}
  @media (max-width: 760px){
    body{overflow:auto}
    .shell{grid-template-columns:1fr;grid-template-rows:minmax(380px,58vh) minmax(440px,1fr)}
    .rail{border-left:none;border-top:1px solid var(--line)}
    header{padding:12px}
    .brand h1,.brand p{display:none}
    .logo{height:56px}
    .rules{padding:9px 12px}
    .rules-note{display:none}
    .stage{padding:12px}
    .stage-head{align-items:flex-start}
    .quick-stat{min-width:auto;padding:7px 9px}
    .quick-stat span{display:none}
    .frame-bar{flex-direction:column;align-items:flex-start}
  }
  @media (max-width: 430px){
    .quick-stat:last-child{display:none}
    .live{padding:6px 9px}
    .stage-title h2{font-size:16px}
    .filters{grid-template-columns:1fr}
    .span-2{grid-column:auto}
  }
  @media (prefers-reduced-motion:reduce){
    *{scroll-behavior:auto!important;animation:none!important;transition:none!important}
  }
</style>
</head>
<body>
<header>
  <div class="brand">
    <img class="logo" src="/brand/schott-vision.jpg" alt="SCHOTT Vision — Visão computacional com IA">
    <div>
      <h1>Monitor de EPI</h1>
      <p>Capacete, colete e óculos</p>
    </div>
  </div>
  <div class="header-meta">
    <div class="live">
      <span class="live-dot" id="live-dot"></span>
      <span id="status-text">Conectando...</span>
    </div>
    <span id="alert-badge" class="zero" title="Infrações ativas">0</span>
  </div>
</header>

<div class="shell">
  <section class="stage">
    <div class="stage-head">
      <div>
        <div class="eyebrow">Monitoramento em tempo real</div>
        <div class="stage-title">
          <h2>Visão da câmera</h2>
          <span class="camera-pill" id="camera-name">CAM-01</span>
        </div>
      </div>
      <label class="camera-select">Câmera
        <select id="camera-select" onchange="selectListedCamera(this.value)"></select>
      </label>
      <div class="quick-stats" aria-label="Resumo operacional">
        <div class="quick-stat danger">
          <span>Alertas ativos</span><strong id="stat-alerts">0</strong>
        </div>
        <div class="quick-stat">
          <span>EPIs exigidos</span><strong id="stat-required">0</strong>
        </div>
      </div>
    </div>
    <div class="stage-frame">
      <img id="camera-stream" src="/video_feed" alt="Imagem da câmera com as detecções">
      <div class="stream-state" id="stream-state">
        <div><strong>Stream indisponível</strong><span>Verifique a conexão da câmera.</span></div>
      </div>
      <div class="frame-bar">
        <div><strong id="clock">--:--:--</strong><span class="meta" id="last-update"> · aguardando dados</span></div>
        <div class="legend">
          <span><i class="swatch" style="background:#3dce86"></i>Com EPI</span>
          <span><i class="swatch" style="background:#ff5d6c"></i>Sem EPI</span>
          <span><i class="swatch" style="background:#07adf2"></i>Equipamento</span>
        </div>
      </div>
    </div>
    <div class="rules" aria-label="Configuração de EPIs obrigatórios">
      <span class="rules-label">Obrigatórios</span>
      <div class="ppe-picks" id="ppe-picks"></div>
      <span class="rules-note" id="rules-note" aria-live="polite"></span>
    </div>
  </section>

  <aside class="rail">
    <section class="alerts">
      <div class="panel-head">
        <h2>Situação agora</h2>
        <span class="panel-count" id="panel-alert-count">0</span>
      </div>
      <div class="ppe-status" id="ppe-status">
        <div class="ppe-chip"><span>Capacete</span><strong>—</strong></div>
        <div class="ppe-chip"><span>Colete</span><strong>—</strong></div>
        <div class="ppe-chip"><span>Óculos</span><strong>—</strong></div>
      </div>
      <div id="alert-list"><p class="no-alerts">Nenhum alerta.</p></div>
    </section>

    <section class="workspace">
      <nav class="tabs" role="tablist" aria-label="Ferramentas">
        <button class="active" role="tab" aria-selected="true" onclick="showTab('history', this)">Histórico</button>
        <button role="tab" aria-selected="false" onclick="showTab('thresholds', this)">Limiares</button>
        <button role="tab" aria-selected="false" onclick="showTab('report', this)">Relatório</button>
        <button role="tab" aria-selected="false" onclick="showTab('admin', this)">Câmeras</button>
      </nav>
      <div class="panels">
        <div id="tab-history" class="tab-content active">
          <div class="filters">
            <label>Data<input type="date" id="h-date"></label>
            <label>Câmera<input type="text" id="h-cam" placeholder="CAM-01"></label>
            <label class="span-2">EPI
              <select id="h-ppe">
                <option value="">Todos</option>
                <option value="helmet">Capacete</option>
                <option value="vest">Colete</option>
                <option value="glasses">Óculos</option>
                <option value="mask">Máscara</option>
                <option value="gloves">Luvas</option>
                <option value="boots">Botas</option>
              </select>
            </label>
            <div class="span-2 actions"><button class="btn" onclick="loadHistory()">Filtrar</button></div>
          </div>
          <div class="table-wrap">
          <table>
            <thead><tr><th>Pessoa</th><th>Câmera</th><th>Motivo</th><th>Quando</th></tr></thead>
            <tbody id="history-body"><tr><td colspan="4" style="color:var(--muted);text-align:center">Carregando...</td></tr></tbody>
          </table>
          </div>
        </div>

        <div id="tab-thresholds" class="tab-content">
          <p class="hint">Sensibilidade de cada EPI. Mais alto exige mais certeza antes de marcar o equipamento.</p>
          <div id="threshold-rows"></div>
          <button class="btn" onclick="saveThresholds(this)">Salvar limiares</button>
        </div>

        <div id="tab-report" class="tab-content">
          <div class="filters">
            <label>De<input type="date" id="r-start"></label>
            <label>Até<input type="date" id="r-end"></label>
            <div class="span-2 actions"><button class="btn" onclick="loadReport()">Gerar</button></div>
          </div>
          <div id="report-kpis" class="kpi-grid" style="display:none">
            <div class="kpi"><div class="value" id="r-violations">–</div><div class="label">Infrações</div></div>
            <div class="kpi"><div class="value" id="r-compliance" style="color:var(--ok)">–</div><div class="label">Conformidade</div></div>
          </div>
          <div class="actions">
            <button class="btn-ghost" onclick="downloadReport('pdf')">Baixar PDF</button>
            <button class="btn-ghost" onclick="downloadReport('excel')">Baixar Excel</button>
          </div>
        </div>

        <div id="tab-admin" class="tab-content">
          <p class="hint">Escolha uma câmera detectada neste computador ou conecte uma câmera IP.</p>
          <div class="cam-list" id="local-cameras"></div>
          <div class="filters">
            <label class="span-2">Câmera IP<input type="text" id="new-rtsp" placeholder="rtsp://192.168.1.10/stream ou 192.168.1.10"></label>
            <div class="span-2 actions"><button class="btn" onclick="connectIpCamera()">Conectar câmera IP</button></div>
          </div>
        </div>
      </div>
    </section>
  </aside>
</div>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<script>
const PPE_CLASSES = ["helmet","vest","glasses","mask","gloves","boots"];
const PPE_LABELS = {
  helmet: "Capacete", vest: "Colete", glasses: "Óculos",
  mask: "Máscara", gloves: "Luvas", boots: "Botas"
};
let thresholdValues = {};
let reportPeriod = {start:"", end:""};
let requiredPpe = [];
let cameraChoices = [];
let activeCameraSource = "";
let toastTimer;

function esc(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  })[ch]);
}

function showToast(message, isError) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = "toast"; }, 2600);
}

function emptyRow(message, cols) {
  return "<tr><td colspan='" + cols + "'><div class='empty-state'>" +
    "<span class='empty-icon'>◎</span>" + esc(message) + "</div></td></tr>";
}

function ppeLabel(name) {
  if (!name) return "–";
  const raw = String(name).trim();
  const missing = raw.toLowerCase().startsWith("sem ");
  const key = raw.toLowerCase().replace(/^sem\\s+/, "");
  const label = PPE_LABELS[key] || raw;
  return missing ? "Sem " + label.toLowerCase() : label;
}

function renderPpeStatus(alerts) {
  const box = document.getElementById("ppe-status");
  if (!box) return;
  if (!requiredPpe.length) {
    box.innerHTML = "<p class='no-alerts'>Nenhum EPI obrigatório. Marque acima o que deve ser cobrado.</p>";
    return;
  }
  const missing = new Set((alerts || []).map(a => String(a.ppe_type || a.reason || "").toLowerCase().replace(/^sem\\s+/, "")));
  box.innerHTML = requiredPpe.map(cls => {
    const bad = missing.has(cls);
    return "<div class='ppe-chip " + (bad ? "bad" : "good") + "'><span>" +
      esc(ppeLabel(cls)) + "</span><strong>" + (bad ? "Ausente" : "Ok") + "</strong></div>";
  }).join("");
}

function renderRequiredPicks() {
  const box = document.getElementById("ppe-picks");
  const sub = document.querySelector(".brand p");
  if (sub) {
    sub.textContent = requiredPpe.length ? requiredPpe.map(ppeLabel).join(", ") : "Nenhum EPI obrigatório";
  }
  document.getElementById("stat-required").textContent = requiredPpe.length;
  if (!box) return;
  box.innerHTML = PPE_CLASSES.map(cls => {
    const on = requiredPpe.indexOf(cls) >= 0;
    return "<button type='button' class='pick" + (on ? " on" : "") +
      "' data-ppe='" + cls + "' onclick='toggleRequired(this)'>" + ppeLabel(cls) + "</button>";
  }).join("");
}

function loadRequired() {
  return fetch("/api/required-ppe")
    .then(r => r.json())
    .then(data => {
      requiredPpe = data.required || [];
      if (data.camera_id) document.getElementById("camera-name").textContent = data.camera_id;
      renderRequiredPicks();
    })
    .catch(() => renderRequiredPicks());
}

function toggleRequired(button) {
  const cls = button.getAttribute("data-ppe");
  const next = requiredPpe.filter(item => item !== cls);
  if (next.length === requiredPpe.length) next.push(cls);
  const ordered = PPE_CLASSES.filter(item => next.indexOf(item) >= 0);
  fetch("/api/required-ppe", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({required: ordered})
  })
    .then(r => r.json().then(data => ({ok: r.ok, data: data})))
    .then(res => {
      const note = document.getElementById("rules-note");
      if (!res.ok) {
        if (note) note.textContent = res.data.error || "Não foi possível salvar";
        showToast(res.data.error || "Não foi possível atualizar os EPIs.", true);
        return;
      }
      requiredPpe = res.data.required || ordered;
      renderRequiredPicks();
      if (note) {
        note.textContent = "Atualizado";
        setTimeout(() => { if (note.textContent === "Atualizado") note.textContent = ""; }, 1600);
      }
      showToast("Regras de EPI atualizadas.");
      loadAlerts();
    })
    .catch(() => showToast("Falha de comunicação ao atualizar as regras.", true));
}

function tickClock() {
  const el = document.getElementById("clock");
  if (el) el.textContent = new Date().toLocaleTimeString("pt-BR");
}

// ── Inicialização ────────────────────────────────────────────────────────────
// O stream MJPEG não dispara window.onload, então a página inicia aqui.
function boot() {
  const today = new Date().toISOString().slice(0,10);
  const first = today.slice(0,8)+"01";
  document.getElementById("r-start").value = first;
  document.getElementById("r-end").value   = today;
  document.getElementById("h-date").value  = today;
  tickClock();
  loadRequired().then(loadAlerts);
  loadHistory();
  loadThresholds();
  loadCameras();
  setInterval(loadAlerts, 2000);
  setInterval(tickClock, 1000);
  const stream = document.getElementById("camera-stream");
  stream.addEventListener("load", () => document.getElementById("stream-state").classList.remove("visible"));
  stream.addEventListener("error", () => document.getElementById("stream-state").classList.add("visible"));
}
boot();

// ── Tabs ─────────────────────────────────────────────────────────────────────
function showTab(name, button) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll("nav.tabs button").forEach(b => b.classList.remove("active"));
  document.getElementById("tab-"+name).classList.add("active");
  if (button) {
    button.classList.add("active");
    document.querySelectorAll("nav.tabs button").forEach(b => b.setAttribute("aria-selected", b === button ? "true" : "false"));
  }
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
      document.getElementById("stat-alerts").textContent = data.length;
      document.getElementById("panel-alert-count").textContent = data.length;
      document.getElementById("last-update").textContent = " · atualizado agora";
      const live = activeCameraSource !== "none";
      document.getElementById("status-text").textContent = live ? "Ao vivo" : "Sem câmera";
      document.getElementById("live-dot").classList.toggle("off", !live);
      renderPpeStatus(data);
      if (data.length === 0) {
        list.innerHTML = "<p class='no-alerts'>Nenhuma infração ativa neste momento.</p>";
        return;
      }
      list.innerHTML = data.map(a => {
        const ts = a.timestamp ? new Date(a.timestamp).toLocaleTimeString("pt-BR") : "–";
        return "<div class='alert-item'>" +
          "<div class='alert-top'><span class='tag tag-red'>" + esc(ppeLabel(a.ppe_type||a.reason)) +
          "</span><span class='meta'>" + esc(ts) + "</span></div>" +
          "<div class='who'>Pessoa " + esc(a.person_id) + "</div>" +
          "<div class='meta'>" + esc(a.camera_id||"Câmera") + "</div></div>";
      }).join("");
    })
    .catch(() => {
      document.getElementById("status-text").textContent = "Sem conexão";
      document.getElementById("live-dot").classList.add("off");
      document.getElementById("last-update").textContent = " · dados indisponíveis";
    });
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
        body.innerHTML = emptyRow("Nenhuma ocorrência encontrada para estes filtros.", 4);
        return;
      }
      body.innerHTML = data.map(i => {
        const ts = i.timestamp ? new Date(i.timestamp).toLocaleString("pt-BR") : "–";
        return "<tr><td>Pessoa " + esc(i.person_id||"–") + "</td><td>" + esc(i.camera_id||"–") +
          "</td><td><span class='tag tag-red'>" + esc(ppeLabel(i.reason||i.ppe_type)) +
          "</span></td><td>" + esc(ts) + "</td></tr>";
      }).join("");
    })
    .catch(() => {
      document.getElementById("history-body").innerHTML = emptyRow("Não foi possível carregar o histórico.", 4);
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
          "<label>" + ppeLabel(cls) + "</label>" +
          "<input type='range' min='0.1' max='1' step='0.05' value='" + val +
          "' id='th-" + cls + "' oninput='this.nextElementSibling.textContent=parseFloat(this.value).toFixed(2)'>" +
          "<span class='val' id='th-v-" + cls + "'>" + val + "</span></div>";
      }).join("");
    });
}

function saveThresholds(button) {
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
    if (!button) return;
    button.textContent = "Salvo";
    showToast("Limiares salvos com sucesso.");
    setTimeout(() => button.textContent = "Salvar limiares", 1500);
  }).catch(() => showToast("Não foi possível salvar os limiares.", true));
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
    })
    .catch(() => showToast("Não foi possível gerar o relatório.", true));
}

function downloadReport(fmt) {
  if (!reportPeriod.start) { loadReport(); return; }
  window.location = "/api/report/" + fmt + "?start=" + reportPeriod.start + "&end=" + reportPeriod.end;
}

// ── Câmeras ──────────────────────────────────────────────────────────────────
function renderCameraLists(data) {
  const devices = data.devices || [];
  cameraChoices = devices;
  activeCameraSource = data.active ? String(data.active.source) : "";
  const sel = document.getElementById("camera-select");
  sel.replaceChildren();
  devices.forEach(d => {
    const opt = document.createElement("option");
    opt.value = String(d.source);
    opt.textContent = d.label;
    if (String(d.source) === activeCameraSource) opt.selected = true;
    sel.appendChild(opt);
  });
  const pill = document.getElementById("camera-name");
  if (pill && data.active) pill.textContent = data.active.label || data.active.id || "Câmera";
  const list = document.getElementById("local-cameras");
  if (!list) return;
  list.replaceChildren();
  const detected = devices.filter(d => d.kind === "local" || d.kind === "ip");
  if (!detected.length) {
    const note = document.createElement("p");
    note.className = "hint";
    note.textContent = "Nenhuma câmera local detectada. Conecte uma câmera IP abaixo.";
    list.appendChild(note);
  }
  devices.forEach(d => {
    const row = document.createElement("div");
    const current = String(d.source) === activeCameraSource;
    row.className = "cam-row" + (current ? " on" : "");
    const text = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = d.label;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = d.kind === "ip" ? "Câmera IP" : d.kind === "none" ? "Sem captura de vídeo" : "Detectada neste computador";
    text.append(title, meta);
    const button = document.createElement("button");
    button.type = "button";
    button.className = current ? "btn btn-ghost" : "btn";
    button.textContent = current ? "Em uso" : "Usar";
    button.onclick = () => selectListedCamera(d.source);
    row.append(text, button);
    list.appendChild(row);
  });
}

function loadCameras() {
  return fetch("/api/cameras/available")
    .then(r => r.json())
    .then(renderCameraLists)
    .catch(() => showToast("Não foi possível listar as câmeras.", true));
}

function selectListedCamera(source) {
  if (source == null || source === "" || String(source) === activeCameraSource) return;
  const choice = cameraChoices.find(d => String(d.source) === String(source));
  const turningOff = String(source) === "none";
  showToast(turningOff ? "Desligando a câmera..." : "Conectando à câmera...");
  fetch("/api/cameras/select", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({source: source, camera_id: choice ? choice.id : ""})
  })
    .then(r => r.json().then(data => ({ok: r.ok, data: data})))
    .then(res => {
      if (!res.ok) {
        showToast(res.data.error || "Não foi possível abrir a câmera.", true);
        loadCameras();
        return;
      }
      showToast(turningOff ? "Nenhuma câmera em uso." : "Câmera em uso: " + (res.data.label || source));
      loadCameras();
    })
    .catch(() => showToast("Falha de comunicação ao trocar a câmera.", true));
}

function connectIpCamera() {
  const url = document.getElementById("new-rtsp").value.trim();
  if (!url) return;
  showToast("Conectando à câmera IP...");
  fetch("/api/cameras/select", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({source: url})
  })
    .then(r => r.json().then(data => ({ok: r.ok, data: data})))
    .then(res => {
      if (!res.ok) {
        showToast(res.data.error || "Não foi possível abrir a câmera IP.", true);
        return;
      }
      document.getElementById("new-rtsp").value = "";
      showToast("Câmera IP conectada.");
      loadCameras();
    })
    .catch(() => showToast("Falha de comunicação ao conectar a câmera IP.", true));
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
        required = set(_s().required_ppe)
        alerts = []
        for a in _s().monitor.get_active_alerts():
            raw = str(a.ppe_type or "").lower()
            if raw.startswith("sem "):
                raw = raw[4:]
            if raw not in required:
                continue
            alerts.append({
                "person_id": a.person_id,
                "ppe_type":  a.ppe_type,
                "camera_id": a.camera_id,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            })
        return jsonify(alerts)

    @app.route("/api/required-ppe", methods=["GET"])
    def api_get_required_ppe():
        return jsonify({
            "required": list(_s().required_ppe),
            "available": list(KNOWN_PPE),
            "camera_id": _s().camera_id,
        })

    @app.route("/api/required-ppe", methods=["POST"])
    def api_set_required_ppe():
        data = request.get_json(silent=True) or {}
        items = data.get("required")
        if not isinstance(items, list):
            return jsonify({"error": "Campo 'required' deve ser uma lista"}), 400
        try:
            saved = _s().set_required_ppe([str(item) for item in items])
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 422
        return jsonify({"ok": True, "required": saved})

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

    def _active_source(state) -> str:
        if state.camera_source is None:
            return NO_CAMERA
        return str(state.camera_source)

    def _camera_catalog():
        state = _s()
        devices = [{
            "id": "NONE",
            "source": NO_CAMERA,
            "label": "Nenhuma câmera",
            "kind": "none",
        }]
        devices.extend(list_local_cameras())
        seen = {item["source"] for item in devices}
        for cam in state.cam_manager.list_all():
            if cam.rtsp_url in seen:
                continue
            devices.append({
                "id": cam.id,
                "source": cam.rtsp_url,
                "label": cam.rtsp_url,
                "kind": "ip",
            })
            seen.add(cam.rtsp_url)
        active_source = _active_source(state)
        if active_source not in seen:
            devices.insert(0, {
                "id": state.camera_id,
                "source": active_source,
                "label": state.camera_label or label_for_source(state.camera_source),
                "kind": "ip" if not active_source.isdigit() else "local",
            })
        return devices

    @app.route("/api/cameras/available")
    def api_cameras_available():
        state = _s()
        return jsonify({
            "active": {
                "id": state.camera_id,
                "source": _active_source(state),
                "label": state.camera_label or state.camera_id,
                "status": state.camera_status,
                "error": state.camera_error,
            },
            "devices": _camera_catalog(),
        })

    @app.route("/api/cameras/select", methods=["POST"])
    def api_select_camera():
        state = _s()
        pipeline = state.pipeline
        if pipeline is None:
            return jsonify({"error": "O monitoramento ainda não está pronto."}), 503
        data = request.get_json(silent=True) or {}
        raw = data.get("source", data.get("rtsp_url"))
        try:
            source = parse_source("" if raw is None else str(raw))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        if source is None:
            camera_id = "NONE"
            label = "Nenhuma câmera"
        elif isinstance(source, str):
            saved = state.cam_manager.find_by_url(source) or state.cam_manager.register(source)
            camera_id = str(data.get("camera_id") or saved.id)
            label = source
        else:
            known = {int(item["source"]): item for item in list_local_cameras()}
            camera_id = str(data.get("camera_id") or f"USB-{source}")
            label = known.get(source, {}).get("label") or label_for_source(source)
        token = pipeline.request_switch(source, camera_id, label)
        status = pipeline.wait_for_switch(token, 12)
        if status == "timeout":
            return jsonify({"error": "A câmera demorou para responder."}), 422
        if status not in {"live", "idle"} or state.camera_source != source:
            return jsonify({
                "error": state.camera_error or "Não foi possível abrir a câmera.",
            }), 422
        return jsonify({
            "ok": True,
            "id": state.camera_id,
            "source": _active_source(state),
            "label": state.camera_label,
        })

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

    @app.route("/brand/schott-vision.jpg")
    def brand_logo():
        path = os.path.join(os.path.dirname(__file__), "static", "schott-vision.jpg")
        return send_file(path, mimetype="image/jpeg")

    @app.route("/")
    def index():
        return Response(_HTML, mimetype="text/html; charset=utf-8")

    return app
