Feature: US-012 – Configurar regras por ambiente
  Como administrador
  Quero definir quais EPIs são obrigatórios em cada local
  Para que o sistema reflita as normas da operação

  Scenario: Configurar regra específica para uma câmera
    Given que o administrador acessa a configuração da câmera "CAM-01"
    When define que o EPI "capacete" é obrigatório para essa câmera
    Then a câmera "CAM-01" passa a exigir o uso de capacete nas detecções

  Scenario: Câmeras distintas podem ter regras diferentes
    Given que "CAM-01" exige apenas capacete
    And "CAM-02" exige capacete e colete
    When o sistema avalia conformidade em cada câmera
    Then "CAM-01" alerta apenas ausência de capacete
    And "CAM-02" alerta ausência de capacete ou de colete

  Scenario: Configurar combinação de múltiplos EPIs obrigatórios
    Given que o administrador acessa a configuração da câmera "CAM-03"
    When define como obrigatórios os EPIs "capacete, colete, óculos"
    Then a câmera "CAM-03" exige os três EPIs simultaneamente para conformidade
