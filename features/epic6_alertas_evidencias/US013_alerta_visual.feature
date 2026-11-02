Feature: US-013 – Exibir alerta visual
  Como operador
  Quero visualizar imediatamente uma não conformidade
  Para que eu possa agir rapidamente

  Scenario: Pessoa em não conformidade é destacada em vermelho
    Given que uma não conformidade de EPI é detectada para a pessoa de ID "5"
    When o quadro de vídeo é renderizado
    Then a caixa delimitadora da pessoa de ID "5" é exibida na cor vermelha

  Scenario: Motivo do alerta é exibido na tela
    Given que uma não conformidade de EPI é detectada para a pessoa de ID "5"
    When o quadro de vídeo é renderizado
    Then o motivo do alerta, como "sem capacete", é exibido próximo à caixa delimitadora
