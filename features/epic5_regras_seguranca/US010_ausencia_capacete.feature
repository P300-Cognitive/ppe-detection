Feature: US-010 – Identificar ausência de capacete
  Como responsável pela segurança
  Quero ser alertado quando uma pessoa estiver sem capacete
  Para que riscos sejam reduzidos

  Scenario: Emitir alerta após confirmação configurável
    Given que uma pessoa é detectada sem capacete
    And o limiar de confirmação está configurado como "5" quadros consecutivos
    When a pessoa permanece sem capacete por "5" quadros consecutivos
    Then o sistema emite um alerta de ausência de capacete

  Scenario: Não emitir alerta antes da confirmação
    Given que uma pessoa é detectada sem capacete
    And o limiar de confirmação está configurado como "5" quadros consecutivos
    When a pessoa está sem capacete por apenas "3" quadros consecutivos
    Then nenhum alerta de ausência de capacete é emitido

  Scenario: Alerta identifica qual pessoa está sem capacete
    Given que "3" pessoas estão no quadro e apenas a de ID "2" está sem capacete
    When o sistema emite o alerta de ausência de capacete
    Then o alerta indica especificamente a pessoa de ID "2" como infratora
