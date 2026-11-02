Feature: US-018 – Consultar histórico de ocorrências
  Como responsável pela segurança
  Quero pesquisar ocorrências passadas
  Para que possa realizar auditorias

  Scenario: Filtrar ocorrências por data
    Given que existem ocorrências registradas em diferentes datas
    When o responsável aplica filtro por data "2026-06-19"
    Then apenas as ocorrências do dia "2026-06-19" são exibidas

  Scenario: Filtrar ocorrências por câmera
    Given que existem ocorrências registradas em múltiplas câmeras
    When o responsável aplica filtro pela câmera "CAM-02"
    Then apenas as ocorrências da câmera "CAM-02" são exibidas

  Scenario: Filtrar ocorrências por tipo de EPI
    Given que existem ocorrências de diferentes tipos de EPI
    When o responsável aplica filtro pelo tipo "capacete"
    Then apenas as ocorrências relacionadas à ausência de "capacete" são exibidas
