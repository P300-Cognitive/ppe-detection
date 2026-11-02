"""Step definitions – Épico 7: Dashboard e Monitoramento (US-017, US-018, US-019)."""
import os
from datetime import date
from behave import given, when, then

try:
    from src.dashboard.monitor import DashboardMonitor
except ImportError:
    DashboardMonitor = None

try:
    from src.reports.history import IncidentHistory
except ImportError:
    IncidentHistory = None

try:
    from src.reports.generator import ReportGenerator
except ImportError:
    ReportGenerator = None


def _make_incident(camera_id, ppe_type, incident_date):
    from types import SimpleNamespace
    return SimpleNamespace(camera_id=camera_id, ppe_type=ppe_type, date=incident_date)


# ── US-017: Visualizar câmeras em tempo real ──────────────────────────────

@given('que "{n}" câmeras estão cadastradas e ativas no sistema')
def step_n_cameras_active(context, n):
    assert DashboardMonitor is not None, \
        "Implemente src.dashboard.monitor.DashboardMonitor"
    context.camera_count = int(n)
    context.monitor = DashboardMonitor()
    for i in range(int(n)):
        context.monitor.register_camera(f'CAM-{i + 1:02d}')

@given('que o painel de monitoramento está aberto')
def step_dashboard_open(context):
    assert DashboardMonitor is not None, \
        "Implemente src.dashboard.monitor.DashboardMonitor"
    context.monitor = DashboardMonitor()
    context.monitor.start()

@when('o operador acessa o painel de monitoramento')
def step_access_dashboard(context):
    context.dashboard_view = context.monitor.get_current_view()

@when('uma não conformidade de EPI é detectada em qualquer câmera')
def step_noncompliance_any_camera(context):
    from types import SimpleNamespace
    context.monitor.push_alert(SimpleNamespace(
        camera_id='CAM-01', person_id=1, reason='sem capacete'
    ))

@then('o painel exibe os streams de todas as "{n}" câmeras simultaneamente')
def step_dashboard_shows_all_cameras(context, n):
    assert context.dashboard_view is not None, \
        "get_current_view() deve retornar o estado do painel"
    assert len(context.dashboard_view.active_streams) == int(n), (
        f"Painel deve exibir {n} câmeras, exibe: "
        f"{len(context.dashboard_view.active_streams)}"
    )

@then('o alerta é exibido no painel em tempo real sem necessidade de atualização manual')
def step_realtime_alert_on_dashboard(context):
    alerts = context.monitor.get_active_alerts()
    assert len(alerts) > 0, \
        "Nenhum alerta encontrado no painel após evento de não conformidade"


# ── US-018: Consultar histórico de ocorrências ────────────────────────────

@given('que existem ocorrências registradas em diferentes datas')
def step_incidents_multiple_dates(context):
    assert IncidentHistory is not None, \
        "Implemente src.reports.history.IncidentHistory"
    context.history = IncidentHistory()
    context.history.add(_make_incident('CAM-01', 'helmet', date(2026, 6, 19)))
    context.history.add(_make_incident('CAM-01', 'vest',   date(2026, 6, 18)))

@given('que existem ocorrências registradas em múltiplas câmeras')
def step_incidents_multiple_cameras(context):
    assert IncidentHistory is not None, \
        "Implemente src.reports.history.IncidentHistory"
    context.history = IncidentHistory()
    context.history.add(_make_incident('CAM-01', 'helmet', date(2026, 6, 19)))
    context.history.add(_make_incident('CAM-02', 'vest',   date(2026, 6, 19)))

@given('que existem ocorrências de diferentes tipos de EPI')
def step_incidents_multiple_ppe_types(context):
    assert IncidentHistory is not None, \
        "Implemente src.reports.history.IncidentHistory"
    context.history = IncidentHistory()
    context.history.add(_make_incident('CAM-01', 'helmet', date(2026, 6, 19)))
    context.history.add(_make_incident('CAM-01', 'vest',   date(2026, 6, 19)))

@when('o responsável aplica filtro por data "{filter_date}"')
def step_filter_by_date(context, filter_date):
    context.filtered = context.history.filter(date=filter_date)

@when('o responsável aplica filtro pela câmera "{camera_id}"')
def step_filter_by_camera(context, camera_id):
    context.filtered = context.history.filter(camera_id=camera_id)

@when('o responsável aplica filtro pelo tipo "{ppe_type}"')
def step_filter_by_ppe_type(context, ppe_type):
    context.filtered = context.history.filter(ppe_type=ppe_type)

@then('apenas as ocorrências do dia "{filter_date}" são exibidas')
def step_only_date_results(context, filter_date):
    assert all(str(i.date) == filter_date for i in context.filtered), (
        f"Resultados fora do filtro de data '{filter_date}': "
        f"{[str(i.date) for i in context.filtered]}"
    )

@then('apenas as ocorrências da câmera "{camera_id}" são exibidas')
def step_only_camera_results(context, camera_id):
    assert all(i.camera_id == camera_id for i in context.filtered), (
        f"Resultados de outras câmeras presentes: "
        f"{[i.camera_id for i in context.filtered]}"
    )

@then('apenas as ocorrências relacionadas à ausência de "{ppe_type}" são exibidas')
def step_only_ppe_type_results(context, ppe_type):
    assert all(i.ppe_type == ppe_type for i in context.filtered), (
        f"Resultados de outros tipos de EPI presentes: "
        f"{[i.ppe_type for i in context.filtered]}"
    )


# ── US-019: Gerar relatórios ──────────────────────────────────────────────

@given('que o gestor seleciona o período de "{start}" a "{end}"')
def step_select_period(context, start, end):
    assert ReportGenerator is not None, \
        "Implemente src.reports.generator.ReportGenerator"
    context.generator = ReportGenerator()
    context.report_start = start
    context.report_end = end

@given('que o relatório de um período foi gerado')
def step_report_already_generated(context):
    assert ReportGenerator is not None, \
        "Implemente src.reports.generator.ReportGenerator"
    context.generator = ReportGenerator()
    context.report = context.generator.generate(
        start='2026-06-01', end='2026-06-30'
    )

@when('solicita a geração do relatório')
def step_generate_report(context):
    context.report = context.generator.generate(
        start=context.report_start, end=context.report_end
    )

@when('o gestor visualiza o relatório')
def step_view_report(context):
    pass  # o relatório já está em context.report

@when('o gestor solicita exportação em formato PDF')
def step_export_pdf(context):
    context.export_path = context.generator.export_pdf(context.report)

@when('o gestor solicita exportação em formato Excel')
def step_export_excel(context):
    context.export_path = context.generator.export_excel(context.report)

@then('o relatório exibe indicadores de conformidade apenas para o período selecionado')
def step_report_period_correct(context):
    assert context.report.start == context.report_start, \
        f"Período inicial incorreto: {context.report.start}"
    assert context.report.end == context.report_end, \
        f"Período final incorreto: {context.report.end}"

@then('o relatório contém a quantidade total de infrações no período')
def step_report_has_violations_count(context):
    assert hasattr(context.report, 'total_violations'), \
        "Relatório deve ter atributo 'total_violations'"
    assert isinstance(context.report.total_violations, int), \
        "total_violations deve ser inteiro"

@then('o relatório exibe a taxa percentual de conformidade no período')
def step_report_has_compliance_rate(context):
    assert hasattr(context.report, 'compliance_rate'), \
        "Relatório deve ter atributo 'compliance_rate'"
    assert 0.0 <= context.report.compliance_rate <= 100.0, \
        f"compliance_rate deve estar entre 0 e 100: {context.report.compliance_rate}"

@then('o sistema gera e disponibiliza o download do arquivo PDF')
def step_pdf_available(context):
    assert context.export_path is not None, \
        "export_pdf() deve retornar o caminho do arquivo"
    assert context.export_path.endswith('.pdf'), \
        f"Arquivo deve ter extensão .pdf: {context.export_path}"
    assert os.path.isfile(context.export_path), \
        f"Arquivo PDF não encontrado em: {context.export_path}"

@then('o sistema gera e disponibiliza o download do arquivo Excel')
def step_excel_available(context):
    assert context.export_path is not None, \
        "export_excel() deve retornar o caminho do arquivo"
    assert context.export_path.endswith(('.xlsx', '.xls')), \
        f"Arquivo deve ter extensão .xlsx: {context.export_path}"
    assert os.path.isfile(context.export_path), \
        f"Arquivo Excel não encontrado em: {context.export_path}"
