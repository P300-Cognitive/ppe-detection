Feature: US-022 – Configurar limiares de confiança
  Como administrador
  Quero ajustar a sensibilidade das detecções
  Para que seja possível reduzir falsos positivos e falsos negativos

  Scenario: Configurar limiar por classe de EPI
    Given que o administrador acessa as configurações de limiares
    When define o limiar de confiança da classe "capacete" como "0.75"
    Then o sistema passa a usar "0.75" como confiança mínima para detectar capacetes

  Scenario: Classes diferentes podem ter limiares distintos
    Given que o limiar de "capacete" é "0.75"
    And o limiar de "colete" é "0.60"
    When o sistema realiza detecções no quadro
    Then aplica limiar "0.75" para capacetes e "0.60" para coletes independentemente

  Scenario: Alterar limiar sem reinicializar o sistema
    Given que o sistema está em execução monitorando câmeras
    When o administrador altera o limiar de confiança da classe "óculos" para "0.80"
    Then a alteração é aplicada imediatamente sem interromper o processamento de vídeo
