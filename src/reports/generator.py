"""Geração de relatórios de conformidade EPI com exportação para PDF e Excel."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.models import Report


class ReportGenerator:
    """Gera relatórios de conformidade por período e exporta para PDF/Excel."""

    def __init__(self, output_dir: str = "reports"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, start: str, end: str) -> Report:
        """Cria relatório para o período. Em produção consultar IncidentHistory."""
        return Report(
            start=start,
            end=end,
            total_violations=0,
            compliance_rate=100.0,
        )

    def export_pdf(self, report: Any) -> str:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as _canvas

        safe_start = report.start.replace("-", "")
        safe_end = report.end.replace("-", "")
        path = str(self._output_dir / f"report_{safe_start}_{safe_end}.pdf")

        c = _canvas.Canvas(path, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Relatório de Conformidade EPI")
        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Período: {report.start} a {report.end}")
        c.drawString(50, 700, f"Total de infrações: {report.total_violations}")
        c.drawString(50, 680, f"Taxa de conformidade: {report.compliance_rate:.1f}%")
        c.save()
        return path

    def export_excel(self, report: Any) -> str:
        from openpyxl import Workbook

        safe_start = report.start.replace("-", "")
        safe_end = report.end.replace("-", "")
        path = str(self._output_dir / f"report_{safe_start}_{safe_end}.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Conformidade EPI"
        ws.append(["Período início", "Período fim", "Total infrações", "Conformidade (%)"])
        ws.append([report.start, report.end, report.total_violations, report.compliance_rate])
        wb.save(path)
        return path
