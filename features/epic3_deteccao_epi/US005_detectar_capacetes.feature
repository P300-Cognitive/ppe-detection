Feature: US-005 – Detectar capacetes
  Como responsável pela segurança
  Quero identificar capacetes na imagem
  Para que o sistema valide o uso correto do EPI

  Scenario: Detectar capacete com caixa delimitadora
    Given que um quadro de vídeo contém uma pessoa usando capacete
    When o sistema analisa o quadro
    Then uma caixa delimitadora é desenhada ao redor do capacete detectado

  Scenario: Exibir confiança da detecção do capacete
    Given que um capacete é detectado no quadro
    When o sistema exibe o resultado da detecção
    Then o valor de confiança da detecção é exibido junto à caixa delimitadora

  Scenario: Detectar capacete amarelo
    Given que um quadro contém um capacete de cor amarela
    When o sistema analisa o quadro
    Then o capacete amarelo é detectado com caixa delimitadora

  Scenario: Detectar capacete branco
    Given que um quadro contém um capacete de cor branca
    When o sistema analisa o quadro
    Then o capacete branco é detectado com caixa delimitadora

  Scenario: Detectar capacete azul
    Given que um quadro contém um capacete de cor azul
    When o sistema analisa o quadro
    Then o capacete azul é detectado com caixa delimitadora
