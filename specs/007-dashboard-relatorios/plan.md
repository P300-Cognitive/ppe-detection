# Plano 007: Dashboard, histórico e relatórios

**Spec:** [spec.md](spec.md)

## Implementação atual

| Módulo | Responsabilidade |
|---|---|
| [src/dashboard/app.py](../../src/dashboard/app.py) | Flask: rotas REST, stream MJPEG e página única embutida no código |
| [src/dashboard/state.py](../../src/dashboard/state.py) | `AppState`: estado compartilhado e último quadro |
| [src/dashboard/monitor.py](../../src/dashboard/monitor.py) | `DashboardMonitor`: lista de câmeras e de alertas |
| [src/reports/history.py](../../src/reports/history.py) | `IncidentHistory`: lista em memória com filtros |
| [src/reports/generator.py](../../src/reports/generator.py) | `ReportGenerator`: valores do relatório e exportação |

## API atual

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Página com as abas Histórico, Limiares, Relatório e Admin |
| GET | `/video_feed` | Stream MJPEG de uma câmera |
| GET | `/api/alerts` | Alertas ativos |
| GET | `/api/history` | Histórico, com `?date=&camera_id=&ppe_type=` |
| GET, POST | `/api/thresholds` | Limiares (ver [spec 008](../008-administracao/spec.md)) |
| GET, POST | `/api/cameras` | Câmeras (ver [spec 008](../008-administracao/spec.md)) |
| GET | `/api/report` | Relatório JSON, com `?start=&end=` |
| GET | `/api/report/pdf`, `/api/report/excel` | Download do relatório |

## Pontos técnicos relevantes

- **Relatório fixo:** `ReportGenerator.generate` retorna `total_violations=0` e `compliance_rate=100.0`, sem consultar nada. O arquivo `reports/report_20260601_20260630.xlsx` confirma: 0 infrações e 100%.
- **Filtros incompatíveis:** o fluxo grava `Violation`, que tem `timestamp` e `reason`. `IncidentHistory.filter` lê `.date` e `.ppe_type`, que não existem nela, e gera `AttributeError`. Confirmado por script. Os cenários passam porque usam `SimpleNamespace` com esses campos.
- **Tipos divergentes:** `Violation`, `Alert` e `Event` representam quase a mesma coisa. `push_alert` coloca o motivo inteiro ("sem helmet") em `ppe_type`.
- **Uma câmera só:** `AppState` guarda um único quadro e `/video_feed` não recebe parâmetro de câmera. O `DashboardMonitor` não recebe câmeras no fluxo de produção.
- **Alertas sem saída:** nada de produção chama `clear_alerts`, então a lista só cresce. O mesmo vale para o histórico.
- **Sem persistência:** `sqlalchemy` e `flask-sqlalchemy` estão declarados, mas nenhum código os importa.
- **Página embutida:** o HTML, o CSS e o JavaScript ficam em uma string de cerca de 360 linhas em `app.py`.
- **Atualização por consulta periódica:** os alertas são buscados a cada 2 s.
- **Sem autenticação:** ver [009/FR-008](../009-orquestracao-plataforma/spec.md).

## Testes

Os 10 cenários passam, mas nenhum usa o Flask nem os tipos de produção:

| Cenário | Limitação |
|---|---|
| Várias câmeras | Conta os nomes registrados em `DashboardMonitor` |
| Filtros | Usa `SimpleNamespace`, que esconde o erro real. Um resultado vazio também passaria |
| Relatório | Verifica o tipo e a faixa dos valores, então os números fixos passam |
| Exportação | Verifica que o arquivo existe, não o conteúdo |

## Verificação contra a constituição

| Princípio | Situação |
|---|---|
| II. Aceitação executável | Violado: os cenários não usam tipos reais nem a API |
| III. Estado honesto | **Violação grave:** valor fixo favorável apresentado como resultado |
| VI. Privacidade | Violado: dashboard sem autenticação |
| VIII. Módulos coesos | Violado: tipos duplicados e página dentro do código Python |

## Direção proposta

1. **Modelo único de ocorrência:** um tipo `Incident` em `src/core/models.py`, com pessoa, câmera, EPI, início, fim e caminhos das evidências.
2. **Persistência:** SQLite com SQLAlchemy, já que o projeto o declara. `IncidentHistory` passa a consultar o banco.
3. **Relatórios reais:** `ReportGenerator` recebe o histórico. Enquanto a fórmula da taxa não for decidida, ou sem dados no período, exibir "indisponível".
4. **Várias câmeras:** um fluxo por câmera, quadro por câmera no `AppState` e `/video_feed/<camera_id>`.
5. **Testes de API:** usar o cliente de testes do Flask nos cenários.
