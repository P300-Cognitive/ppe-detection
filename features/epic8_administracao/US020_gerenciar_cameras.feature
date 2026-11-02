Feature: US-020 – Gerenciar câmeras
  Como administrador
  Quero cadastrar e remover câmeras
  Para que o ambiente seja configurado facilmente

  Scenario: Cadastrar câmera com URL RTSP
    Given que o administrador acessa o módulo de gerenciamento de câmeras
    When cadastra uma nova câmera com URL RTSP "rtsp://192.168.1.100/stream"
    Then a câmera é registrada no sistema com a URL fornecida

  Scenario: Testar conectividade da câmera cadastrada
    Given que uma câmera com URL RTSP está cadastrada
    When o administrador solicita teste de conectividade
    Then o sistema retorna o status de conectividade da câmera

  Scenario: Habilitar câmera desabilitada
    Given que uma câmera está com status desabilitado
    When o administrador habilita a câmera
    Then a câmera passa para o status habilitado e começa a ser monitorada

  Scenario: Desabilitar câmera ativa
    Given que uma câmera está com status habilitado
    When o administrador desabilita a câmera
    Then a câmera para de ser monitorada sem ser removida do sistema
