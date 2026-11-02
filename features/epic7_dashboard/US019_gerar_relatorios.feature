Feature: US-019 – Gerar relatórios
  Como gestor de segurança
  Quero visualizar indicadores de conformidade
  Para que possa acompanhar a evolução da operação

  Scenario: Gerar relatório por período
    Given que o gestor seleciona o período de "2026-06-01" a "2026-06-30"
    When solicita a geração do relatório
    Then o relatório exibe indicadores de conformidade apenas para o período selecionado

  Scenario: Relatório exibe quantidade de infrações
    Given que o relatório de um período foi gerado
    When o gestor visualiza o relatório
    Then o relatório contém a quantidade total de infrações no período

  Scenario: Relatório exibe taxa de conformidade
    Given que o relatório de um período foi gerado
    When o gestor visualiza o relatório
    Then o relatório exibe a taxa percentual de conformidade no período

  Scenario: Exportar relatório para PDF
    Given que o relatório de um período foi gerado
    When o gestor solicita exportação em formato PDF
    Then o sistema gera e disponibiliza o download do arquivo PDF

  Scenario: Exportar relatório para Excel
    Given que o relatório de um período foi gerado
    When o gestor solicita exportação em formato Excel
    Then o sistema gera e disponibiliza o download do arquivo Excel
