Feature: US-002 – Processar vídeo em tempo real
  Como operador do sistema
  Quero que os quadros sejam processados continuamente
  Para que a análise de EPI ocorra sem intervenção manual

  Scenario: Processamento inicia automaticamente após conexão
    Given que a câmera está conectada e exibindo vídeo
    When a conexão com a câmera é estabelecida
    Then o processamento de quadros inicia automaticamente sem intervenção manual

  Scenario: Sistema mantém taxa mínima de FPS
    Given que o processamento de vídeo está em execução
    And a taxa mínima de FPS está configurada como "15"
    When os quadros são capturados continuamente
    Then o sistema mantém pelo menos "15" FPS durante o processamento

  Scenario: Sistema continua operando com pequena perda de quadros
    Given que o processamento de vídeo está em execução
    When ocorre uma pequena perda de quadros no stream
    Then o sistema continua processando os quadros seguintes sem interrupção
