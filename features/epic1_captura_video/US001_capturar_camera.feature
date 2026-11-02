Feature: US-001 – Capturar vídeo de uma câmera
  Como operador do sistema
  Quero conectar uma câmera ao sistema
  Para que as imagens possam ser analisadas automaticamente

  Scenario: Conectar câmera USB com sucesso
    Given que uma câmera USB está conectada à porta do sistema
    When o operador inicia a captura de vídeo
    Then o sistema exibe o vídeo em tempo real

  Scenario: Conectar câmera via RTSP com sucesso
    Given que uma URL de stream RTSP válida está configurada
    When o operador inicia a captura de vídeo
    Then o sistema exibe o vídeo em tempo real

  Scenario: Câmera USB indisponível
    Given que nenhuma câmera USB está conectada ao sistema
    When o operador tenta iniciar a captura de vídeo
    Then o sistema informa falha de conexão com a câmera

  Scenario: Stream RTSP inacessível
    Given que a URL de stream RTSP está inacessível
    When o operador tenta iniciar a captura de vídeo
    Then o sistema informa falha de conexão com a câmera
