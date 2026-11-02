Feature: US-011 – Identificar ausência de colete
  Como responsável pela segurança
  Quero ser alertado quando uma pessoa estiver sem colete
  Para que medidas corretivas sejam tomadas

  Scenario: Emitir alerta apenas após validação de ausência
    Given que uma pessoa é detectada sem colete
    And o limiar de confirmação está configurado como "5" quadros consecutivos
    When a pessoa permanece sem colete por "5" quadros consecutivos
    Then o sistema emite um alerta de ausência de colete

  Scenario: Registrar evento de ausência de colete
    Given que o sistema emitiu um alerta de ausência de colete para a pessoa de ID "3"
    When o alerta é processado
    Then o evento é registrado no sistema com identificador da pessoa, câmera e timestamp
