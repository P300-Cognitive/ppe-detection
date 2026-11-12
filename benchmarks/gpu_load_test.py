#!/usr/bin/env python3
"""Prova de carga de GPU — P300 Vision Safety.

Valida as premissas do capacity.md numa GPU local (ex.: RTX 5080).

Etapas:
  prepare  Gera clipe de teste (ou usa gravações reais) e exporta TensorRT FP16/INT8.
  infer    Throughput puro de inferência por modelo, precisão e batch.
  decode   Quantos streams 1080p a CPU (PyAV) ou o NVDEC sustentam.
  e2e      Simula N câmeras em tempo real (decode → pose 5 fps → EPI em recortes
           a 2 Hz por pessoa) e encontra o maior N que cumpre o SLO.

Exemplos:
  python gpu_load_test.py prepare
  python gpu_load_test.py infer
  python gpu_load_test.py decode --backend cpu nvdec --streams 25 50 100
  python gpu_load_test.py e2e --cams 25 50 75 100 --persons 2
  python gpu_load_test.py e2e --cams 50 --persons 5 --videos D:/gravacoes
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
import platform
import queue
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
MODELS = ROOT / "models"
RESULTS = ROOT / "results"
IMG = 640
SLOT_BYTES = 8 + IMG * IMG * 3  # 8 bytes de sequência + imagem letterbox 640x640 BGR
SYNTH_CLIP = DATA / "synthetic_1080p15.mp4"


# ════════════════════════════════════════════════════════════════════════
# Utilidades
# ════════════════════════════════════════════════════════════════════════

def pct(values, q):
    if not values:
        return float("nan")
    s = sorted(values)
    k = (len(s) - 1) * q / 100
    f = math.floor(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def letterbox(img: np.ndarray, size: int = IMG) -> np.ndarray:
    import cv2
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    nh, nw = max(1, round(h * r)), max(1, round(w * r))
    out = np.full((size, size, 3), 114, np.uint8)
    top, left = (size - nh) // 2, (size - nw) // 2
    out[top:top + nh, left:left + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    return out


def video_paths(videos: str | None) -> list[str]:
    if videos:
        p = Path(videos)
        files = [p] if p.is_file() else sorted(
            f for f in p.rglob("*") if f.suffix.lower() in {".mp4", ".mkv", ".avi", ".mov", ".ts", ".h264", ".h265"}
        )
        if not files:
            sys.exit(f"Nenhum vídeo encontrado em {videos}")
        return [str(f) for f in files]
    if not SYNTH_CLIP.exists():
        sys.exit(f"{SYNTH_CLIP} não existe. Rode 'prepare' antes ou passe --videos.")
    return [str(SYNTH_CLIP)]


def save_result(kind: str, payload: dict) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{kind}_{datetime.now():%Y%m%d_%H%M%S}.json"
    if isinstance(payload.get("args"), dict):
        payload["args"] = {k: v for k, v in payload["args"].items() if not callable(v)}
    payload = {"kind": kind, "host": host_info(), **payload}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultado salvo em {path}")
    return path


def host_info() -> dict:
    import psutil
    info = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor(),
        "cpu_logical": psutil.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
    }
    try:
        import pynvml
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(h)
        info["gpu"] = name.decode() if isinstance(name, bytes) else name
        info["gpu_vram_mb"] = pynvml.nvmlDeviceGetMemoryInfo(h).total // 2**20
        drv = pynvml.nvmlSystemGetDriverVersion()
        info["driver"] = drv.decode() if isinstance(drv, bytes) else drv
    except Exception:
        pass
    return info


def table(rows: list[dict], cols: list[str]) -> str:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.1f}"
        return str(v)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(fmt(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


class Sampler(threading.Thread):
    """Amostra GPU, NVDEC, VRAM, CPU e RAM do sistema em segundo plano."""

    def __init__(self, interval: float = 0.5):
        super().__init__(daemon=True)
        import psutil
        import pynvml
        pynvml.nvmlInit()
        self.nv, self.ps = pynvml, psutil
        self.h = pynvml.nvmlDeviceGetHandleByIndex(0)
        self.base_vram = pynvml.nvmlDeviceGetMemoryInfo(self.h).used
        self.base_ram = psutil.virtual_memory().used
        self.interval = interval
        self.samples: list[dict] = []
        self._halt = threading.Event()
        psutil.cpu_percent(None)

    def run(self):
        while not self._halt.wait(self.interval):
            try:
                u = self.nv.nvmlDeviceGetUtilizationRates(self.h)
                m = self.nv.nvmlDeviceGetMemoryInfo(self.h)
                dec = self.nv.nvmlDeviceGetDecoderUtilization(self.h)[0]
            except Exception:
                continue
            self.samples.append({
                "gpu": u.gpu, "nvdec": dec, "vram": m.used,
                "cpu": self.ps.cpu_percent(None), "ram": self.ps.virtual_memory().used,
            })

    def reset(self):
        self.samples.clear()

    def stop(self):
        self._halt.set()
        self.join(2)

    def summary(self) -> dict:
        s = self.samples
        if not s:
            return {}
        col = lambda k: [x[k] for x in s]
        return {
            "gpu_util_avg": round(sum(col("gpu")) / len(s), 1),
            "gpu_util_p95": round(pct(col("gpu"), 95), 1),
            "nvdec_util_avg": round(sum(col("nvdec")) / len(s), 1),
            "vram_peak_mb": round(max(col("vram")) / 2**20),
            "vram_delta_mb": round((max(col("vram")) - self.base_vram) / 2**20),
            "cpu_avg": round(sum(col("cpu")) / len(s), 1),
            "cpu_p95": round(pct(col("cpu"), 95), 1),
            "ram_delta_gb": round((max(col("ram")) - self.base_ram) / 2**30, 2),
        }


# ════════════════════════════════════════════════════════════════════════
# Decodificadores (CPU via PyAV, GPU via PyNvVideoCodec/NVDEC)
#
# Todos os frames são decodificados (H.264/H.265 exige), mas a conversão para
# BGR só acontece nos frames amostrados — é assim que o servidor real deve operar.
# ════════════════════════════════════════════════════════════════════════

class CpuDecoder:
    def __init__(self, path: str):
        self.path = path
        self._it = self._frames()

    def _frames(self):
        import av
        while True:
            with av.open(self.path) as c:
                st = c.streams.video[0]
                st.codec_context.thread_count = 1  # 1 núcleo por stream, como em produção
                for f in c.decode(st):
                    yield f

    def next(self):
        return next(self._it)

    @staticmethod
    def to_bgr(frame) -> np.ndarray:
        return frame.to_ndarray(format="bgr24")


class NvDecoder:
    """Decode na GPU. O frame fica em memória de vídeo; só os amostrados vão para a CPU."""

    def __init__(self, path: str, gpu: int = 0):
        import PyNvVideoCodec as nvc
        self.nvc, self.path, self.gpu = nvc, path, gpu
        self._it = self._frames()

    def _frames(self):
        nvc = self.nvc
        while True:
            dmx = nvc.CreateDemuxer(filename=self.path)
            dec = nvc.CreateDecoder(gpuid=self.gpu, codec=dmx.GetNvCodecId(),
                                    cudacontext=0, cudastream=0, usedevicememory=True)
            self.width, self.height = dmx.Width(), dmx.Height()
            for packet in dmx:
                for frame in dec.Decode(packet):
                    yield frame
            del dec, dmx

    def next(self):
        return next(self._it)

    def to_bgr(self, frame) -> np.ndarray:
        import cv2
        import torch
        # NV12 na GPU → host → BGR. Só ocorre nos frames amostrados.
        nv12 = torch.from_dlpack(frame).cpu().numpy()
        nv12 = nv12.reshape(self.height * 3 // 2, self.width)
        return cv2.cvtColor(nv12, cv2.COLOR_YUV2BGR_NV12)


def make_decoder(backend: str, path: str):
    return NvDecoder(path) if backend == "nvdec" else CpuDecoder(path)


# ════════════════════════════════════════════════════════════════════════
# prepare
# ════════════════════════════════════════════════════════════════════════

def make_clip(path: Path, seconds: int, fps: int, bitrate: int, w: int = 1920, h: int = 1080):
    """Clipe sintético com textura, ruído e 'pessoas' em movimento, para o encoder gastar bitrate real."""
    import av
    import cv2
    rng = np.random.default_rng(0)
    texture = cv2.resize(rng.integers(40, 200, (h // 8, w // 8 + 64, 3), dtype=np.uint8),
                         (w + 512, h), interpolation=cv2.INTER_CUBIC)
    people = [(rng.integers(0, w - 260), rng.integers(200, h - 640), rng.integers(-6, 7)) for _ in range(5)]
    path.parent.mkdir(parents=True, exist_ok=True)
    codec = "libx264"
    with av.open(str(path), "w") as c:
        try:
            st = c.add_stream(codec, rate=fps)
        except Exception:
            codec = "libopenh264"
            st = c.add_stream(codec, rate=fps)
        st.width, st.height, st.pix_fmt, st.bit_rate = w, h, "yuv420p", bitrate
        if codec == "libx264":
            st.options = {"g": str(fps * 2), "bf": "0", "preset": "veryfast"}
        for i in range(seconds * fps):
            off = (i * 2) % 512
            img = np.ascontiguousarray(texture[:, off:off + w])
            noise = rng.integers(-12, 13, (h // 2, w // 2, 1), dtype=np.int16)
            img = np.clip(img.astype(np.int16) + cv2.resize(noise, (w, h))[..., None], 0, 255).astype(np.uint8)
            for j, (x, y, dx) in enumerate(people):
                xx = int((x + dx * i) % (w - 260))
                cv2.rectangle(img, (xx, y), (xx + 260, y + 640), (30 + 40 * j, 80, 200 - 30 * j), -1)
                cv2.circle(img, (xx + 130, y + 70), 60, (180, 200, 220), -1)
            for p in st.encode(av.VideoFrame.from_ndarray(img, format="bgr24")):
                c.mux(p)
        for p in st.encode():
            c.mux(p)
    print(f"Clipe gerado: {path} ({seconds}s, {w}x{h}@{fps}, {bitrate // 1000} kbps, {codec})")


def make_calibration(paths: list[str], n: int = 128) -> Path:
    """Imagens para calibração INT8. Para medir throughput qualquer imagem serve;
    para avaliar acurácia, use frames reais da planta (--videos)."""
    import cv2
    out = DATA / "calib" / "images" / "val"
    out.mkdir(parents=True, exist_ok=True)
    existing = list(out.glob("*.jpg"))
    if len(existing) >= n:
        return out.parent.parent
    per_video = math.ceil(n / len(paths))
    k = 0
    for p in paths:
        dec = CpuDecoder(p)
        for i in range(per_video * 5):
            f = dec.next()
            if i % 5 == 0:
                cv2.imwrite(str(out / f"calib_{k:04d}.jpg"), letterbox(CpuDecoder.to_bgr(f)))
                k += 1
    return out.parent.parent


def write_calib_yaml(root: Path, names: dict, pose: bool) -> Path:
    cfg = {"path": str(root), "train": "images/val", "val": "images/val",
           "names": {int(k): str(v) for k, v in names.items()}}
    if pose:
        cfg["kpt_shape"] = [17, 3]
        cfg["flip_idx"] = [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15]
    path = root / ("calib_pose.yaml" if pose else "calib_det.yaml")
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")  # JSON é YAML válido
    return path


def cmd_prepare(a):
    if not a.videos and (a.force or not SYNTH_CLIP.exists()):
        make_clip(SYNTH_CLIP, a.clip_seconds, a.camera_fps, a.bitrate)
    paths = video_paths(a.videos)
    calib_root = make_calibration(paths) if "int8" in a.precisions else None

    MODELS.mkdir(parents=True, exist_ok=True)
    os.chdir(MODELS)  # a ultralytics baixa os .pt para o diretório atual
    from ultralytics import YOLO

    for name in [a.pose_model, a.ppe_model]:
        for prec in a.precisions:
            out = MODELS / f"{Path(name).stem}_{prec}_b{a.max_batch}.engine"
            if out.exists() and not a.force:
                print(f"OK (já existe): {out.name}")
                continue
            model = YOLO(name)
            kw = dict(format="engine", imgsz=IMG, dynamic=True, batch=a.max_batch,
                      workspace=a.workspace, device=0, simplify=True, verbose=False)
            if prec == "fp16":
                kw["half"] = True
            else:
                kw["int8"] = True
                kw["data"] = str(write_calib_yaml(calib_root, model.names, "pose" in name))
            print(f"Exportando {name} → {prec} (batch dinâmico até {a.max_batch}) ...")
            t0 = time.time()
            produced = Path(model.export(**kw))
            produced.replace(out)
            print(f"  {out.name} em {time.time() - t0:.0f}s")
    print("\nPreparação concluída.")


# ════════════════════════════════════════════════════════════════════════
# Inferência (TensorRT via AutoBackend, pré-processamento na GPU)
# ════════════════════════════════════════════════════════════════════════

class Engine:
    def __init__(self, path: Path):
        import torch
        from ultralytics.nn.autobackend import AutoBackend
        try:
            from ultralytics.utils.nms import non_max_suppression
        except ImportError:
            from ultralytics.utils.ops import non_max_suppression
        self.torch = torch
        self.path = path
        self.name = path.stem
        self.is_pose = "pose" in path.stem
        self.backend = AutoBackend(str(path), device=torch.device("cuda:0"), fp16=path.suffix == ".pt", verbose=False)
        self.nc = len(self.backend.names)
        self.nms = non_max_suppression

    def __call__(self, batch_u8, nms: bool = True):
        """batch_u8: tensor uint8 (B,640,640,3) BGR já na GPU. Retorna detecções após NMS."""
        x = batch_u8.permute(0, 3, 1, 2).flip(1)  # BHWC BGR → BCHW RGB
        x = (x.half() if self.backend.fp16 else x.float()).div_(255).contiguous()
        y = self.backend(x)
        if isinstance(y, (list, tuple)):
            y = y[0]
        return self.nms(y, 0.25, 0.45, nc=self.nc) if nms else y


def engine_files(patterns: list[str] | None) -> list[Path]:
    files = sorted(MODELS.glob("*.engine"))
    if patterns:
        files = [f for f in files if any(p in f.stem for p in patterns)]
    if not files:
        sys.exit("Nenhum .engine em benchmarks/models. Rode 'prepare' antes.")
    return files


def sample_frames(paths: list[str], n: int = 64) -> np.ndarray:
    dec = CpuDecoder(paths[0])
    frames = []
    for i in range(n * 3):
        f = dec.next()
        if i % 3 == 0:
            frames.append(letterbox(CpuDecoder.to_bgr(f)))
    return np.stack(frames)


def cmd_infer(a):
    import torch
    frames = sample_frames(video_paths(a.videos), max(a.batches) * 2)
    host = torch.from_numpy(frames).pin_memory()
    rows = []
    sampler = Sampler(0.2)
    sampler.start()
    for path in engine_files(a.models):
        eng = Engine(path)
        for b in a.batches:
            try:
                for _ in range(3):
                    eng(host[:b].cuda(non_blocking=True), nms=not a.no_nms)
                torch.cuda.synchronize()
            except Exception as exc:
                print(f"  {path.stem} batch {b}: ignorado ({type(exc).__name__}: {exc})")
                continue
            sampler.reset()
            lat, n, i = [], 0, 0
            t_end = time.perf_counter() + a.seconds
            t_start = time.perf_counter()
            while time.perf_counter() < t_end:
                s = (i * b) % (len(host) - b + 1)
                t0 = time.perf_counter()
                eng(host[s:s + b].cuda(non_blocking=True), nms=not a.no_nms)
                torch.cuda.synchronize()
                lat.append((time.perf_counter() - t0) * 1000)
                n += b
                i += 1
            elapsed = time.perf_counter() - t_start
            row = {
                "modelo": path.stem, "batch": b,
                "img_s": n / elapsed, "ms_img": elapsed * 1000 / n,
                "lat_p50_ms": pct(lat, 50), "lat_p95_ms": pct(lat, 95),
                **sampler.summary(),
            }
            rows.append(row)
            print(f"  {path.stem:<28} b={b:<3} {row['img_s']:8.0f} img/s  p95 {row['lat_p95_ms']:6.1f} ms  "
                  f"GPU {row.get('gpu_util_avg', 0):5.1f}%  VRAM {row.get('vram_peak_mb', 0)} MB")
        del eng
        torch.cuda.empty_cache()
    sampler.stop()

    print("\n## Throughput de inferência\n")
    print(table(rows, ["modelo", "batch", "img_s", "ms_img", "lat_p95_ms", "gpu_util_avg", "vram_peak_mb"]))
    estimates = capacity_estimates(rows, a)
    if estimates:
        print("\n## Estimativa de câmeras por GPU (só inferência)\n")
        print(table(estimates, ["precisao", "pessoas", "ms_gpu_por_camera", "cameras_70pct", "cameras_100pct"]))
    save_result("infer", {"args": vars(a), "rows": rows, "capacity": estimates})


def capacity_estimates(rows: list[dict], a) -> list[dict]:
    """Câmeras por GPU = tempo de GPU disponível ÷ tempo de GPU por câmera."""
    best: dict[tuple, float] = {}
    for r in rows:
        stem = r["modelo"]
        kind = "pose" if "pose" in stem else "ppe"
        prec = "int8" if "int8" in stem else "fp16" if "fp16" in stem else "pt"
        best[(kind, prec)] = max(best.get((kind, prec), 0), r["img_s"])
    out = []
    for prec in ("fp16", "int8", "pt"):
        pose_k = ("pose", prec)
        ppe_k = ("ppe", prec) if ("ppe", prec) in best else ("ppe", "fp16")  # INT8 ausente → FP16
        if pose_k not in best or ppe_k not in best:
            continue
        label = prec if ppe_k[1] == prec else f"pose {prec} + EPI {ppe_k[1]}"
        for persons in (2, 5):
            ms = 1000 * (a.infer_fps / best[pose_k] + persons * a.ppe_hz / best[ppe_k])
            out.append({"precisao": label, "pessoas": persons, "ms_gpu_por_camera": ms,
                        "cameras_70pct": int(700 / ms), "cameras_100pct": int(1000 / ms)})
    return out


# ════════════════════════════════════════════════════════════════════════
# decode
# ════════════════════════════════════════════════════════════════════════

def _decode_worker(backend, paths, n_streams, offset, seconds, out_q, convert_every):
    decs = [make_decoder(backend, paths[(offset + i) % len(paths)]) for i in range(n_streams)]
    for d in decs:
        d.next()  # abre o decoder antes de cronometrar
    count, conv = 0, 0
    t_end = time.perf_counter() + seconds
    while time.perf_counter() < t_end:
        for d in decs:
            f = d.next()
            count += 1
            if convert_every and count % convert_every == 0:
                d.to_bgr(f)
                conv += 1
    out_q.put((count, conv))


def cmd_decode(a):
    paths = video_paths(a.videos)
    rows = []
    for backend in a.backend:
        for n in a.streams:
            procs_n = min(n, a.procs or (os.cpu_count() if backend == "cpu" else 4))
            per = [n // procs_n + (1 if i < n % procs_n else 0) for i in range(procs_n)]
            q = mp.Queue()
            sampler = Sampler(0.5)
            sampler.start()
            procs, off = [], 0
            for k in per:
                p = mp.Process(target=_decode_worker,
                               args=(backend, paths, k, off, a.seconds, q, round(a.camera_fps / a.infer_fps)))
                p.start()
                procs.append(p)
                off += k
            results = [q.get() for _ in procs]
            for p in procs:
                p.join()
            sampler.stop()
            total = sum(r[0] for r in results)
            fps = total / a.seconds
            row = {"backend": backend, "streams": n, "processos": procs_n,
                   "fps_total": fps, "fps_necessario": n * a.camera_fps,
                   "streams_sustentaveis": int(fps / a.camera_fps), **sampler.summary()}
            rows.append(row)
            print(f"  {backend:<6} {n:>4} streams: {fps:8.0f} fps → sustenta {row['streams_sustentaveis']} "
                  f"@ {a.camera_fps} fps  CPU {row.get('cpu_avg', 0):5.1f}%  NVDEC {row.get('nvdec_util_avg', 0):5.1f}%  "
                  f"VRAM +{row.get('vram_delta_mb', 0)} MB")
    print("\n## Capacidade de decode (sem limite de tempo real)\n")
    print(table(rows, ["backend", "streams", "fps_total", "fps_necessario", "streams_sustentaveis",
                       "cpu_avg", "nvdec_util_avg", "vram_delta_mb"]))
    save_result("decode", {"args": vars(a), "rows": rows})


# ════════════════════════════════════════════════════════════════════════
# e2e — N câmeras em tempo real
#
# Workers (processos) decodificam cada câmera no ritmo real, amostram a 5 fps,
# fazem letterbox e escrevem num ring buffer em memória compartilhada.
# O processo principal agrupa em batch e infere pose + EPI na GPU.
# ════════════════════════════════════════════════════════════════════════

def _person_boxes(persons: int, w: int, h: int) -> list[tuple[int, int, int, int]]:
    bw, bh = int(w * 0.14), int(h * 0.6)
    step = (w - bw) // max(persons, 1)
    return [(i * step, h // 5, i * step + bw, h // 5 + bh) for i in range(persons)]


def _cam_worker(wid, cams, backend, paths, cfg, shm_name, slots, msg_q, stop, stats):
    from multiprocessing import shared_memory
    shm = shared_memory.SharedMemory(name=shm_name)
    ring = np.ndarray((slots, SLOT_BYTES), np.uint8, buffer=shm.buf)
    decs = {c: make_decoder(backend, paths[c % len(paths)]) for c in cams}
    for d in decs.values():
        d.next()
    pose_every = max(1, round(cfg["camera_fps"] / cfg["infer_fps"]))
    ppe_every = max(1, round(cfg["camera_fps"] / cfg["ppe_hz"]))
    period = 1.0 / cfg["camera_fps"]
    boxes = None
    slot, seq, idx = 0, 0, 0
    max_lag = 0.0
    next_t = time.perf_counter()

    def emit(kind, cam, img, ts):
        nonlocal slot, seq
        seq += 1
        row = ring[slot]
        row[8:] = letterbox(img).reshape(-1)
        row[:8] = np.frombuffer(np.int64(seq).tobytes(), np.uint8)
        msg_q.put((kind, wid, slot, seq, cam, ts))
        slot = (slot + 1) % slots

    while not stop.is_set():
        for c, d in decs.items():
            f = d.next()
            want_pose = idx % pose_every == 0
            want_ppe = idx % ppe_every == 0
            if not (want_pose or want_ppe):
                continue
            ts = time.time()
            bgr = d.to_bgr(f)
            if boxes is None:
                boxes = _person_boxes(cfg["persons"], bgr.shape[1], bgr.shape[0])
            if want_pose:
                emit("pose", c, bgr, ts)
            if want_ppe:
                for x1, y1, x2, y2 in boxes:
                    emit("ppe", c, bgr[y1:y2, x1:x2], ts)
        idx += 1
        stats[wid * 2] = idx * len(cams)
        next_t += period
        delay = next_t - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        else:
            max_lag = max(max_lag, -delay)
            stats[wid * 2 + 1] = max_lag
    shm.close()


class _Lane:
    """Fila de um modelo (pose ou EPI) com batching, latência e descarte."""

    def __init__(self, name, engine, max_batch, max_wait_ms, max_pending):
        self.name, self.engine = name, engine
        self.max_batch, self.max_wait = max_batch, max_wait_ms / 1000
        self.pending: deque = deque()
        self.cv = threading.Condition()
        self.max_pending = max_pending
        self.done = 0
        self.dropped = 0
        self.ages: list[float] = []
        self.batch_sizes: list[int] = []

    def push(self, item):
        with self.cv:
            self.pending.append(item)
            while len(self.pending) > self.max_pending:  # prioriza frescor: descarta o mais antigo
                self.pending.popleft()
                self.dropped += 1
            self.cv.notify()

    def take(self, stop):
        with self.cv:
            deadline = time.perf_counter() + self.max_wait
            while len(self.pending) < self.max_batch and not stop.is_set():
                left = deadline - time.perf_counter()
                if left <= 0:
                    break
                self.cv.wait(left)
            n = min(self.max_batch, len(self.pending))
            return [self.pending.popleft() for _ in range(n)]


def _run_lane(lane: _Lane, rings: dict, stop: threading.Event, measuring: threading.Event):
    import torch
    host = torch.empty((lane.max_batch, IMG, IMG, 3), dtype=torch.uint8).pin_memory()
    hv = host.numpy()
    while not stop.is_set():
        items = lane.take(stop)
        if not items:
            continue
        ok = []
        for _, wid, slot, seq, cam, ts in items:
            row = rings[wid][slot]
            if int(np.frombuffer(row[:8].tobytes(), np.int64)[0]) != seq:
                if measuring.is_set():
                    lane.dropped += 1  # slot sobrescrito antes de ser consumido
                continue
            hv[len(ok)] = row[8:].reshape(IMG, IMG, 3)
            ok.append(ts)
        if not ok:
            continue
        lane.engine(host[:len(ok)].cuda(non_blocking=True))
        torch.cuda.synchronize()
        now = time.time()
        if measuring.is_set():
            lane.done += len(ok)
            lane.ages.extend((now - ts) * 1000 for ts in ok)
            lane.batch_sizes.append(len(ok))


def run_e2e(n_cams: int, a, pose_eng: "Engine", ppe_eng: "Engine", paths: list[str]) -> dict:
    from multiprocessing import shared_memory
    workers = a.workers or max(1, math.ceil(n_cams / a.cams_per_worker))
    groups = [list(range(n_cams))[i::workers] for i in range(workers)]
    cfg = {"camera_fps": a.camera_fps, "infer_fps": a.infer_fps, "ppe_hz": a.ppe_hz, "persons": a.persons}
    msgs_per_s = [len(g) * (a.infer_fps + a.persons * a.ppe_hz) for g in groups]
    slots = [max(32, int(m * a.ring_seconds)) for m in msgs_per_s]

    shms = [shared_memory.SharedMemory(create=True, size=s * SLOT_BYTES) for s in slots]
    rings = {i: np.ndarray((slots[i], SLOT_BYTES), np.uint8, buffer=shms[i].buf) for i in range(workers)}
    msg_q = mp.Queue()
    stop_w = mp.Event()
    stats = mp.Array("d", workers * 2)

    # Taxas efetivas: os workers amostram 1 a cada N frames (ex.: 15 fps / 8 = 1,875 Hz para EPI)
    eff_pose = a.camera_fps / max(1, round(a.camera_fps / a.infer_fps))
    eff_ppe = a.camera_fps / max(1, round(a.camera_fps / a.ppe_hz))
    target_pose = round(n_cams * eff_pose)
    target_ppe = round(n_cams * a.persons * eff_ppe)
    lanes = {
        "pose": _Lane("pose", pose_eng, a.max_batch, a.max_wait_ms, max(64, int(target_pose * a.max_queue_s))),
        "ppe": _Lane("ppe", ppe_eng, a.max_batch, a.max_wait_ms, max(64, int(target_ppe * a.max_queue_s))),
    }
    stop_t, measuring = threading.Event(), threading.Event()

    def dispatch():
        while not stop_t.is_set():
            try:
                m = msg_q.get(timeout=0.1)
            except queue.Empty:
                continue
            lanes[m[0]].push(m)

    threads = [threading.Thread(target=dispatch, daemon=True)]
    threads += [threading.Thread(target=_run_lane, args=(l, rings, stop_t, measuring), daemon=True)
                for l in lanes.values()]
    for t in threads:
        t.start()

    procs = []
    for i, g in enumerate(groups):
        p = mp.Process(target=_cam_worker,
                       args=(i, g, a.backend, paths, cfg, shms[i].name, slots[i], msg_q, stop_w, stats))
        p.start()
        procs.append(p)

    print(f"\n▶ {n_cams} câmeras | {workers} workers | decode {a.backend} | "
          f"{a.persons} pessoas/câmera | aquecendo {a.warmup}s ...", flush=True)
    time.sleep(a.warmup)
    for i in range(workers):
        stats[i * 2 + 1] = 0.0
    sampler = Sampler(0.5)
    sampler.start()
    decoded0 = sum(stats[i * 2] for i in range(workers))
    for lane in lanes.values():
        lane.dropped = 0  # descartes do aquecimento não contam
    measuring.set()
    t0 = time.time()
    time.sleep(a.seconds)
    measuring.clear()
    elapsed = time.time() - t0
    decoded = sum(stats[i * 2] for i in range(workers)) - decoded0
    worker_lag = max(stats[i * 2 + 1] for i in range(workers))
    sampler.stop()

    stop_w.set()
    for p in procs:
        p.join(5)
        if p.is_alive():
            p.terminate()
    stop_t.set()
    for t in threads:
        t.join(2)
    for s in shms:
        s.close()
        s.unlink()

    res = {"cameras": n_cams, "workers": workers, "pessoas": a.persons, "decode": a.backend,
           "decode_fps": decoded / elapsed, "decode_fps_alvo": n_cams * a.camera_fps,
           "atraso_worker_max_s": round(worker_lag, 2)}
    for name, lane, target in (("pose", lanes["pose"], target_pose), ("ppe", lanes["ppe"], target_ppe)):
        rate = lane.done / elapsed
        total = lane.done + lane.dropped
        res.update({
            f"{name}_inf_s": rate, f"{name}_alvo_s": target,
            f"{name}_atingido_pct": 100 * rate / target if target else 100.0,
            f"{name}_idade_p50_ms": pct(lane.ages, 50), f"{name}_idade_p95_ms": pct(lane.ages, 95),
            f"{name}_descarte_pct": 100 * lane.dropped / total if total else 0.0,
            f"{name}_batch_medio": sum(lane.batch_sizes) / len(lane.batch_sizes) if lane.batch_sizes else 0,
        })
    res.update(sampler.summary())
    fails = []
    for name in ("pose", "ppe"):
        if res[f"{name}_atingido_pct"] < 95:
            fails.append(f"{name} {res[f'{name}_atingido_pct']:.0f}% da taxa")
        if res[f"{name}_idade_p95_ms"] > a.max_latency_ms:
            fails.append(f"{name} p95 {res[f'{name}_idade_p95_ms']:.0f} ms")
        if res[f"{name}_descarte_pct"] > 1:
            fails.append(f"{name} descarte {res[f'{name}_descarte_pct']:.1f}%")
    if res["decode_fps"] < 0.95 * res["decode_fps_alvo"] or worker_lag > 1.0:
        fails.append(f"decode abaixo do tempo real (atraso {worker_lag:.1f}s)")
    res["slo_ok"] = not fails
    res["falhas"] = "; ".join(fails)
    print(f"  pose {res['pose_inf_s']:.0f}/{target_pose} inf/s p95 {res['pose_idade_p95_ms']:.0f} ms | "
          f"EPI {res['ppe_inf_s']:.0f}/{target_ppe} inf/s p95 {res['ppe_idade_p95_ms']:.0f} ms | "
          f"GPU {res.get('gpu_util_avg', 0):.0f}% VRAM {res.get('vram_peak_mb', 0)} MB "
          f"CPU {res.get('cpu_avg', 0):.0f}% RAM +{res.get('ram_delta_gb', 0)} GB → "
          f"{'OK' if res['slo_ok'] else 'FALHOU: ' + res['falhas']}", flush=True)
    return res


def cmd_e2e(a):
    paths = video_paths(a.videos)
    def pick(pose: bool) -> Path | None:
        for prec in (a.precision, "fp16"):  # INT8 ausente → FP16
            for f in sorted(MODELS.glob(f"*_{prec}_*.engine")):
                if ("pose" in f.stem) == pose:
                    return f
        return None
    pose_path, ppe_path = pick(True), pick(False)
    if not pose_path or not ppe_path:
        sys.exit(f"Faltam engines {a.precision} de pose e de EPI em {MODELS}. Rode 'prepare'.")
    print(f"Modelos: {pose_path.name} + {ppe_path.name}")
    pose_eng, ppe_eng = Engine(pose_path), Engine(ppe_path)

    rows = []
    for n in a.cams:
        r = run_e2e(n, a, pose_eng, ppe_eng, paths)
        rows.append(r)
        if not r["slo_ok"] and a.stop_on_fail:
            break
    ok = [r["cameras"] for r in rows if r["slo_ok"]]
    print("\n## Resultado ponta a ponta\n")
    print(table(rows, ["cameras", "pose_atingido_pct", "pose_idade_p95_ms", "ppe_atingido_pct",
                       "ppe_idade_p95_ms", "gpu_util_avg", "vram_peak_mb", "cpu_avg", "ram_delta_gb", "slo_ok"]))
    print(f"\nMaior número de câmeras dentro do SLO: {max(ok) if ok else 'nenhum'}")
    save_result("e2e", {"args": vars(a), "rows": rows, "max_cameras_ok": max(ok) if ok else 0})


# ════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════

def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # console do Windows usa cp1252 por padrão
        except Exception:
            pass
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--videos", help="Arquivo ou pasta com gravações reais (padrão: clipe sintético)")
    common.add_argument("--camera-fps", type=int, default=15, help="FPS do stream da câmera")
    common.add_argument("--infer-fps", type=float, default=5, help="FPS de inferência de pose por câmera")
    common.add_argument("--ppe-hz", type=float, default=2, help="Avaliações de EPI por pessoa por segundo")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("prepare", parents=[common], help="Gera clipe e exporta engines TensorRT")
    s.add_argument("--pose-model", default="yolov8s-pose.pt")
    s.add_argument("--ppe-model", default="yolov8s.pt",
                   help="Substituto do modelo de EPI (mesma arquitetura do modelo a ser treinado)")
    s.add_argument("--precisions", nargs="+", default=["fp16", "int8"], choices=["fp16", "int8"])
    s.add_argument("--max-batch", type=int, default=32)
    s.add_argument("--workspace", type=float, default=4, help="GB de workspace do TensorRT")
    s.add_argument("--clip-seconds", type=int, default=30)
    s.add_argument("--bitrate", type=int, default=4_000_000)
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_prepare)

    s = sub.add_parser("infer", parents=[common], help="Throughput puro de inferência")
    s.add_argument("--models", nargs="*", help="Filtra engines por trecho do nome (ex: int8 pose)")
    s.add_argument("--batches", nargs="+", type=int, default=[1, 8, 16, 32])
    s.add_argument("--seconds", type=float, default=10)
    s.add_argument("--no-nms", action="store_true", help="Mede só a rede, sem o NMS (capacidade pura da GPU)")
    s.set_defaults(func=cmd_infer)

    s = sub.add_parser("decode", parents=[common], help="Capacidade de decode CPU vs NVDEC")
    s.add_argument("--backend", nargs="+", default=["cpu", "nvdec"], choices=["cpu", "nvdec"])
    s.add_argument("--streams", nargs="+", type=int, default=[25, 50, 100])
    s.add_argument("--procs", type=int, default=0, help="Processos (padrão: núcleos para CPU, 4 para NVDEC)")
    s.add_argument("--seconds", type=float, default=20)
    s.set_defaults(func=cmd_decode)

    s = sub.add_parser("e2e", parents=[common], help="N câmeras em tempo real")
    s.add_argument("--cams", nargs="+", type=int, default=[25, 50, 75, 100])
    s.add_argument("--persons", type=int, default=2, help="Pessoas simuladas por câmera")
    s.add_argument("--precision", default="int8", choices=["fp16", "int8"])
    s.add_argument("--backend", default="cpu", choices=["cpu", "nvdec"], help="Decoder de vídeo")
    s.add_argument("--workers", type=int, default=0)
    s.add_argument("--cams-per-worker", type=int, default=6)
    s.add_argument("--max-batch", type=int, default=32)
    s.add_argument("--max-wait-ms", type=float, default=30, help="Espera máxima para completar um batch")
    s.add_argument("--max-queue-s", type=float, default=2, help="Fila máxima (em segundos de carga) antes de descartar")
    s.add_argument("--ring-seconds", type=float, default=1.5)
    s.add_argument("--max-latency-ms", type=float, default=1000, help="SLO: idade p95 do frame ao resultado")
    s.add_argument("--warmup", type=float, default=15)
    s.add_argument("--seconds", type=float, default=60)
    s.add_argument("--stop-on-fail", action="store_true")
    s.set_defaults(func=cmd_e2e)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    mp.freeze_support()
    main()
